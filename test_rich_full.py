from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

def get_rainbow_style(index: int) -> str:
    colors = ["red", "orange1", "yellow", "green", "blue", "purple", "violet"]
    return colors[index % len(colors)]

categories_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
categories_table.add_column("☐", width=2)
categories_table.add_column("Task ID", style="dim")
categories_table.add_column("Category")
categories_table.add_column("Task")

color = get_rainbow_style(0)
categories_table.add_row(
    "[ ]", 
    "123", 
    f"[{color}]Personal[/{color}]", 
    f"[{color}]Buy Milk[/{color}]"
)

console.print(categories_table)
