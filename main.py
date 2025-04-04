import os
import json
import flet as ft

CONFIG_FILE = "config.json"


def load_api_key():
    """Load the API key from a JSON configuration file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("api_key", "")
        except Exception as e:
            print("Error loading config:", e)
    return ""


def save_api_key(api_key):
    """Save the API key to a JSON configuration file."""
    config = {"api_key": api_key}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def main(page: ft.Page):
    # Set up page properties
    page.title = "DocuPanda"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    # Welcome message
    welcome_text = ft.Text("Welcome to DocuPanda", style="headlineLarge")

    # Hyperlink to get API key
    api_key_link = ft.TextButton(
        content=ft.Text("Click here to get your API key", style="bodyLarge", color=ft.colors.BLUE),
        on_click=lambda e: page.launch_url("https://www.docupanda.io/settings/general"),
    )

    # Load stored API key if available
    stored_api_key = load_api_key()

    # --- API Key Configuration View ---
    api_key_input = ft.TextField(label="API Key", width=300, value=stored_api_key)

    # Helper function to display snackbars
    def show_snackbar(message):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def save_api_key_click(e):
        api_key = api_key_input.value.strip()
        if api_key:
            save_api_key(api_key)
            show_snackbar("API key saved!")
            show_main_view()
        else:
            show_snackbar("Please enter a valid API key.")

    save_button = ft.ElevatedButton(text="Save API Key", on_click=save_api_key_click)

    config_view = ft.Column(
        controls=[
            ft.Text("Set your API key:", style="headlineMedium"),
            api_key_input,
            api_key_link,
            save_button,
        ],
        alignment="center",
        visible=False
    )

    # --- Main View ---
    upload_button = ft.ElevatedButton(
        text="Upload Dataset",
        on_click=lambda e: show_snackbar("Upload clicked!")
    )
    download_button = ft.ElevatedButton(
        text="Download Dataset Results",
        on_click=lambda e: show_snackbar("Download clicked!")
    )

    main_view = ft.Column(
        controls=[
            welcome_text,
            ft.Text("API key is configured.", style="headlineSmall"),
            ft.Row(controls=[upload_button, download_button], spacing=20),
        ],
        alignment="center",
        visible=False
    )

    # Button to change API key
    def change_api_key_click(e):
        api_key_input.value = load_api_key()
        config_view.visible = True
        main_view.visible = False
        change_key_button.visible = False
        page.update()

    change_key_button = ft.ElevatedButton(
        text="Change API Key", on_click=change_api_key_click, visible=False
    )

    # Toggle views based on whether the API key exists
    def show_main_view():
        current_key = load_api_key()
        if current_key:
            config_view.visible = False
            main_view.visible = True
            change_key_button.visible = True
        else:
            config_view.visible = True
            main_view.visible = False
            change_key_button.visible = False
        page.update()

    # Set initial UI state
    if stored_api_key:
        show_main_view()
    else:
        config_view.visible = True

    page.add(config_view, main_view, change_key_button)


ft.app(target=main)
