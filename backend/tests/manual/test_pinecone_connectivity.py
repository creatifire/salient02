# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Manual test script to verify Pinecone connectivity and API key functionality.

Tests all configured Pinecone API keys in .env and reports on:
- API key validity
- Index accessibility
- Query performance
- Vector count statistics

Each index query has a 30-second timeout to prevent hanging on network issues.

Usage:
    python backend/tests/manual/test_pinecone_connectivity.py [--verbose]
    
    --verbose: Show detailed connection information
"""
import os
import sys
import argparse
import time
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

console = Console()

# Default timeout for index queries (in seconds)
DEFAULT_TIMEOUT = 30


class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeouts."""
    raise TimeoutError("Operation timed out")


def load_environment() -> None:
    """Load environment variables from .env file."""
    env_path = backend_dir.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        console.print(f"[cyan]✅ Loaded environment from {env_path}[/cyan]")
    else:
        console.print(f"[yellow]⚠️  No .env file found at {env_path}[/yellow]")


def discover_pinecone_keys() -> Dict[str, str]:
    """Discover all Pinecone API keys in environment."""
    keys = {}
    
    # Check for primary key
    if os.getenv('PINECONE_API_KEY'):
        keys['PINECONE_API_KEY'] = os.getenv('PINECONE_API_KEY')
    
    # Check for account-specific keys
    # Pattern: PINECONE_API_KEY_<ACCOUNT>
    for key, value in os.environ.items():
        if key.startswith('PINECONE_API_KEY_') and value:
            keys[key] = value
    
    return keys


def test_pinecone_key(key_name: str, api_key: str, verbose: bool = False) -> Dict[str, Any]:
    """Test a single Pinecone API key.
    
    Args:
        key_name: Name of the environment variable
        api_key: The API key value
        verbose: Show detailed information
        
    Returns:
        Dict with test results
    """
    result = {
        'key_name': key_name,
        'status': 'unknown',
        'error': None,
        'indexes': [],
        'total_vectors': 0,
        'duration_ms': 0
    }
    
    start_time = time.time()
    
    try:
        # Import here to catch import errors
        from pinecone import Pinecone
        
        # Initialize client
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        result['indexes'] = [idx.name for idx in indexes]
        
        if verbose:
            console.print(f"[dim]  Found {len(indexes)} index(es) for {key_name}[/dim]")
        
        # Test each index with timeout
        index_details = []
        for idx in indexes:
            try:
                # Set up timeout signal
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(DEFAULT_TIMEOUT)
                
                try:
                    index = pc.Index(idx.name)
                    stats = index.describe_index_stats()
                    
                    index_info = {
                        'name': idx.name,
                        'dimension': idx.dimension,
                        'metric': idx.metric,
                        'host': idx.host,
                        'vectors': stats.total_vector_count,
                        'status': 'accessible'
                    }
                    index_details.append(index_info)
                    result['total_vectors'] += stats.total_vector_count
                    
                    if verbose:
                        console.print(f"[dim]    ✅ {idx.name}: {stats.total_vector_count:,} vectors[/dim]")
                finally:
                    # Cancel the alarm
                    signal.alarm(0)
                    
            except TimeoutError:
                index_info = {
                    'name': idx.name,
                    'status': 'error',
                    'error': f'Timeout after {DEFAULT_TIMEOUT}s'
                }
                index_details.append(index_info)
                
                if verbose:
                    console.print(f"[dim]    ❌ {idx.name}: Timeout after {DEFAULT_TIMEOUT}s[/dim]")
                    
            except Exception as e:
                index_info = {
                    'name': idx.name,
                    'status': 'error',
                    'error': str(e)
                }
                index_details.append(index_info)
                
                if verbose:
                    console.print(f"[dim]    ❌ {idx.name}: {str(e)[:80]}[/dim]")
        
        result['index_details'] = index_details
        
        # Determine overall status
        if not index_details:
            result['status'] = 'no_indexes'
        else:
            accessible_count = sum(1 for idx in index_details if idx['status'] == 'accessible')
            error_count = sum(1 for idx in index_details if idx['status'] == 'error')
            
            if accessible_count > 0 and error_count == 0:
                result['status'] = 'success'
            elif accessible_count > 0 and error_count > 0:
                result['status'] = 'partial'  # Some indexes work, some don't
            else:
                result['status'] = 'error'  # All indexes failed
        
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        
        if verbose:
            console.print(f"[dim]  ❌ Connection error: {str(e)[:100]}[/dim]")
    
    result['duration_ms'] = (time.time() - start_time) * 1000
    return result


def print_summary_table(results: List[Dict[str, Any]]) -> None:
    """Print summary table of all test results."""
    table = Table(
        title="Pinecone Connectivity Test Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("API Key", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Indexes", justify="center")
    table.add_column("Total Vectors", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Error", style="dim")
    
    for result in results:
        status_icon = {
            'success': '✅ PASS',
            'partial': '⚠️  PARTIAL',
            'no_indexes': '⚠️  WARN',
            'error': '❌ FAIL',
            'unknown': '❓ UNKNOWN'
        }.get(result['status'], '❓')
        
        if result['status'] == 'success':
            status_style = "green"
        elif result['status'] in ('no_indexes', 'partial'):
            status_style = "yellow"
        else:
            status_style = "red"
        
        error_msg = result['error'][:50] + '...' if result['error'] and len(result['error']) > 50 else (result['error'] or '')
        
        table.add_row(
            result['key_name'],
            f"[{status_style}]{status_icon}[/{status_style}]",
            str(len(result['indexes'])),
            f"{result['total_vectors']:,}" if result['total_vectors'] > 0 else "-",
            f"{result['duration_ms']:.0f}ms",
            error_msg
        )
    
    console.print()
    console.print(table)


def print_detailed_results(results: List[Dict[str, Any]]) -> None:
    """Print detailed results for each API key."""
    console.print("\n[bold cyan]Detailed Results[/bold cyan]")
    console.print("─" * 80)
    
    for result in results:
        console.print(f"\n[bold]{result['key_name']}[/bold]")
        
        if result['status'] == 'error' and result['error']:
            # Overall connection error (no indexes could be listed)
            console.print(f"  [red]❌ Error: {result['error']}[/red]")
            continue
        
        if result['status'] == 'error' and not result['error']:
            # Index-level errors (indexes listed but all failed)
            console.print(f"  [red]❌ All indexes failed[/red]")
            console.print(f"  [dim]Duration: {result['duration_ms']:.0f}ms[/dim]")
        
        if result['status'] == 'no_indexes':
            console.print(f"  [yellow]⚠️  No indexes found (API key valid but no data)[/yellow]")
            continue
        
        if result['status'] == 'partial':
            accessible_count = sum(1 for idx in result.get('index_details', []) if idx['status'] == 'accessible')
            total_count = len(result.get('index_details', []))
            console.print(f"  [yellow]⚠️  Partial success: {accessible_count}/{total_count} indexes accessible[/yellow]")
            console.print(f"  [dim]Duration: {result['duration_ms']:.0f}ms[/dim]")
        
        if result['status'] == 'success':
            console.print(f"  [green]✅ Connected successfully[/green]")
            console.print(f"  [dim]Duration: {result['duration_ms']:.0f}ms[/dim]")
        
        if 'index_details' in result and result['index_details']:
            console.print(f"\n  [bold]Indexes ({len(result['index_details'])})[/bold]:")
            for idx_detail in result['index_details']:
                if idx_detail['status'] == 'accessible':
                    console.print(f"    [green]✅[/green] {idx_detail['name']}")
                    console.print(f"       Vectors: {idx_detail['vectors']:,}")
                    console.print(f"       Dimension: {idx_detail['dimension']}")
                    console.print(f"       Metric: {idx_detail['metric']}")
                    console.print(f"       Host: {idx_detail['host'][:60]}...")
                else:
                    console.print(f"    [red]❌[/red] {idx_detail['name']}")
                    console.print(f"       Error: {idx_detail.get('error', 'Unknown error')[:100]}")


def main():
    parser = argparse.ArgumentParser(
        description='Test Pinecone API key connectivity and functionality'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed connection information'
    )
    
    args = parser.parse_args()
    
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  PINECONE CONNECTIVITY TEST[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    # Load environment
    load_environment()
    
    # Discover API keys
    console.print("\n[cyan]🔍 Discovering Pinecone API keys...[/cyan]")
    api_keys = discover_pinecone_keys()
    
    if not api_keys:
        console.print("[red]❌ No Pinecone API keys found in environment[/red]")
        console.print("[yellow]Expected keys: PINECONE_API_KEY or PINECONE_API_KEY_<ACCOUNT>[/yellow]")
        sys.exit(1)
    
    console.print(f"[green]✅ Found {len(api_keys)} API key(s):[/green]")
    for key_name in api_keys.keys():
        masked_key = api_keys[key_name][:8] + '...' + api_keys[key_name][-4:] if len(api_keys[key_name]) > 12 else '***'
        console.print(f"   • {key_name}: {masked_key}")
    
    # Test each key
    console.print(f"\n[cyan]🧪 Testing {len(api_keys)} API key(s)...[/cyan]\n")
    results = []
    
    for key_name, api_key in api_keys.items():
        if args.verbose:
            console.print(f"[bold]Testing {key_name}...[/bold]")
        
        result = test_pinecone_key(key_name, api_key, verbose=args.verbose)
        results.append(result)
        
        if not args.verbose:
            # Show progress
            if result['status'] == 'success':
                console.print(f"[green]✅[/green] {key_name}")
            elif result['status'] == 'partial':
                accessible_count = sum(1 for idx in result.get('index_details', []) if idx['status'] == 'accessible')
                total_count = len(result.get('index_details', []))
                console.print(f"[yellow]⚠️[/yellow]  {key_name} ({accessible_count}/{total_count} indexes)")
            elif result['status'] == 'no_indexes':
                console.print(f"[yellow]⚠️[/yellow]  {key_name} (no indexes)")
            else:
                console.print(f"[red]❌[/red] {key_name}")
    
    # Print summary
    print_summary_table(results)
    
    # Print detailed results if verbose
    if args.verbose:
        print_detailed_results(results)
    
    # Overall status
    console.print()
    all_success = all(r['status'] == 'success' for r in results)
    any_error = any(r['status'] == 'error' for r in results)
    any_partial = any(r['status'] == 'partial' for r in results)
    
    if all_success:
        console.print("[bold green]✅ ALL TESTS PASSED[/bold green]")
        console.print("[green]All Pinecone API keys are valid and accessible[/green]")
        sys.exit(0)
    elif any_error:
        console.print("[bold red]❌ SOME TESTS FAILED[/bold red]")
        console.print("[red]One or more Pinecone API keys have connectivity issues[/red]")
        console.print("[yellow]Run with --verbose for detailed error information[/yellow]")
        sys.exit(1)
    elif any_partial:
        console.print("[bold yellow]⚠️  PARTIAL SUCCESS[/bold yellow]")
        console.print("[yellow]Some indexes are accessible but others timed out or failed[/yellow]")
        console.print("[yellow]Run with --verbose for detailed error information[/yellow]")
        sys.exit(0)
    else:
        console.print("[bold yellow]⚠️  WARNINGS DETECTED[/bold yellow]")
        console.print("[yellow]API keys are valid but some indexes may have issues[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()

