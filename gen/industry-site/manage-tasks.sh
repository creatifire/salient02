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
    echo "  list-cancelled      List only cancelled tasks"
    echo "  complete TASK-ID    Mark task as complete (e.g., F01-T1)"
    echo "  incomplete TASK-ID  Mark task as incomplete"
    echo "  cancel TASK-ID      Mark task as cancelled"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 complete F01-T1"
    echo "  $0 list-incomplete"
    echo "  $0 list-cancelled"
    echo "  $0 cancel F01-T4"
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

case "$1" in
    status)
        echo "Task Completion Status:"
        echo "======================"
        total=$(grep -cE '^\*\*\[(x| |CANCELLED)\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE")
        complete=$(grep -cE '^\*\*\[x\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE")
        incomplete=$(grep -cE '^\*\*\[ \] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE")
        cancelled=$(grep -cE '^\*\*\[CANCELLED\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE")
        active=$((total - cancelled))
        
        if [ $active -gt 0 ]; then
            percent=$((complete * 100 / active))
        else
            percent=0
        fi
        
        echo "Total: $total tasks"
        echo "Active: $active tasks"
        echo "Completed: $complete tasks ($percent%)"
        echo "Remaining: $incomplete tasks"
        echo "Cancelled: $cancelled tasks"
        ;;
        
    list)
        echo "All Tasks:"
        echo "=========="
        grep -E '^\*\*\[(x| |CANCELLED)\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE"
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
        
    list-cancelled)
        echo "Cancelled Tasks:"
        echo "==============="
        grep -E '^\*\*\[CANCELLED\] (F|S)[0-9]+-T[0-9]+:' "$PLAN_FILE"
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
        
    cancel)
        if [ $# -ne 2 ]; then
            echo "Error: Task ID required"
            echo "Usage: $0 cancel TASK-ID"
            exit 1
        fi
        
        TASK_ID="$2"
        sed -i '' "s/^\*\*\[ \] ${TASK_ID}:/**[CANCELLED] ${TASK_ID}:/" "$PLAN_FILE"
        echo "✗ Marked $TASK_ID as cancelled"
        
        # Show updated status
        $0 status
        ;;
        
    *)
        echo "Error: Unknown command '$1'"
        usage
        exit 1
        ;;
esac
