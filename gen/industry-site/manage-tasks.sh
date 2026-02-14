#!/bin/bash
# Helper script to manage task checkboxes in site-gen-plan.md

PLAN_FILE="site-gen-plan.md"

usage() {
    echo "Usage: $0 <command> [task-id]"
    echo ""
    echo "Commands:"
    echo "  status              Show completion status"
    echo "  list                List all tasks with status"
    echo "  list-incomplete     List only incomplete tasks"
    echo "  list-complete       List only completed tasks"
    echo "  complete TASK-ID    Mark task as complete (e.g., F01-T1)"
    echo "  incomplete TASK-ID  Mark task as incomplete"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 complete F01-T1"
    echo "  $0 list-incomplete"
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

case "$1" in
    status)
        echo "Task Completion Status:"
        echo "======================"
        total=$(grep -cE '^\*\*\[(x| )\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE")
        complete=$(grep -cE '^\*\*\[x\]' "$PLAN_FILE")
        incomplete=$(grep -cE '^\*\*\[ \]' "$PLAN_FILE")
        percent=$((complete * 100 / total))
        
        echo "Total: $total tasks"
        echo "Completed: $complete tasks ($percent%)"
        echo "Remaining: $incomplete tasks"
        ;;
        
    list)
        echo "All Tasks:"
        echo "=========="
        grep -E '^\*\*\[(x| )\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE"
        ;;
        
    list-incomplete)
        echo "Incomplete Tasks:"
        echo "================"
        grep -E '^\*\*\[ \] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE"
        ;;
        
    list-complete)
        echo "Completed Tasks:"
        echo "==============="
        grep -E '^\*\*\[x\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE"
        ;;
        
    complete)
        if [ $# -ne 2 ]; then
            echo "Error: Task ID required"
            echo "Usage: $0 complete TASK-ID"
            exit 1
        fi
        
        TASK_ID="$2"
        # Escape special characters for sed
        sed -i '' "s/^\*\*\[ \] ${TASK_ID}:/**[x] ${TASK_ID}:/" "$PLAN_FILE"
        echo "✓ Marked $TASK_ID as complete"
        
        # Show updated status
        $0 status
        ;;
        
    incomplete)
        if [ $# -ne 2 ]; then
            echo "Error: Task ID required"
            echo "Usage: $0 incomplete TASK-ID"
            exit 1
        fi
        
        TASK_ID="$2"
        sed -i '' "s/^\*\*\[x\] ${TASK_ID}:/**[ ] ${TASK_ID}:/" "$PLAN_FILE"
        echo "○ Marked $TASK_ID as incomplete"
        
        # Show updated status
        $0 status
        ;;
        
    *)
        echo "Error: Unknown command '$1'"
        usage
        exit 1
        ;;
esac
