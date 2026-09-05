from rich.console import Console
from rich.table import Table
from rich.progress import track
import time

console = Console()
console.print("Starting process...", style="bold blue")
console.print("File loaded successfully", style="green")
console.print("Config missing, using defaults", style="yellow")
console.print("Failed to connect", style="bold red")

# Tables
table = Table(title="Results")
table.add_column("Name")
table.add_column("Status")
table.add_row("Task 1", "[green]✓ Done[/green]")
table.add_row("Task 2", "[red]✗ Failed[/red]")
console.print(table)

for i in track(range(10), description="Processing..."):
    time.sleep(0.1)
