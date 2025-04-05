import json
import os
import platform
import threading
from pathlib import Path

import flet as ft

from dp_desktop.download import download_dataset
from dp_desktop.list_objects import list_schemas, list_dataset_names
from dp_desktop.upload import upload_files

APP_NAME = "DocuPanda"


def get_latest_api_key():
    key = load_api_key()
    return key.strip() if key else ""


def get_config_dir(app_name: str):
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / app_name
    elif system == "Windows":
        return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / app_name
    else:  # Linux and others
        return Path.home() / f".{app_name.lower()}"


CONFIG_DIR = get_config_dir(APP_NAME)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_api_key():
    """Load the API key from our standard config file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("api_key", "")
        except Exception as e:
            print("Error loading config:", e)
    return ""


def save_api_key(api_key):
    """Save the API key to our standard config file."""
    config = {"api_key": api_key}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def main(page: ft.Page):
    page.title = "DocuPanda"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 20

    # --------------------------------------------------------------------
    #  Helper to show a snackbar
    # --------------------------------------------------------------------
    def show_snackbar(message: str):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    # --------------------------------------------------------------------
    #  Shared UI elements (spinner, progress bar, progress text)
    # --------------------------------------------------------------------
    loading_indicator = ft.ProgressRing(visible=False)
    progress_bar = ft.ProgressBar(width=400, visible=False)
    progress_text = ft.Text("", visible=False)

    def show_progress_ui():
        loading_indicator.visible = True
        progress_bar.visible = True
        progress_text.visible = True
        page.update()

    def hide_progress_ui():
        loading_indicator.visible = False
        progress_bar.visible = False
        progress_text.visible = False
        page.update()

    # --------------------------------------------------------------------
    #  UPLOAD finishing/progress/error
    # --------------------------------------------------------------------
    def finish_upload():
        progress_text.value += " Upload complete!"
        hide_progress_ui()

    def progress_callback_upload(files_processed, total_files):
        progress_bar.value = files_processed / total_files
        progress_text.value = f"Uploading {files_processed} of {total_files} files..."
        show_progress_ui()

    def handle_upload_error(file_path, error_msg):
        # Append some note to progress_text (or show_snackbar)
        progress_text.value += f"\nError uploading {file_path.name}: {error_msg}"
        page.update()

    # --------------------------------------------------------------------
    #  DOWNLOAD finishing/progress/error
    # --------------------------------------------------------------------
    def finish_download():
        progress_text.value += " Download complete!"
        hide_progress_ui()

    def progress_callback_download(files_processed, total_files):
        progress_bar.value = files_processed / total_files
        progress_text.value = f"Downloading {files_processed} of {total_files} documents..."
        show_progress_ui()

    def handle_download_error(doc_id_or_path, error_msg):
        progress_text.value += f"\nError downloading {doc_id_or_path}: {error_msg}"
        page.update()

    # --------------------------------------------------------------------
    #  config_view: For entering/saving the API key
    # --------------------------------------------------------------------
    api_key_input = ft.TextField(label="API Key", width=300, value=load_api_key())

    def save_api_key_click(e):
        api_key = api_key_input.value.strip()
        if api_key:
            save_api_key(api_key)
            show_snackbar("API key saved!")
            show_main_view()
        else:
            show_snackbar("Please enter a valid API key.")

    save_button = ft.ElevatedButton("Save API Key", on_click=save_api_key_click)
    api_key_link = ft.TextButton(
        content=ft.Text("Click here to get your API key", style="bodyLarge", color=ft.Colors.BLUE_600),
        on_click=lambda e: page.launch_url("https://www.docupanda.io/settings/general"),
    )

    config_view = ft.Column(
        controls=[
            ft.Text("Set your API key:", style="headlineMedium"),
            api_key_input,
            api_key_link,
            save_button,
        ],
        alignment="center",
        visible=False,
    )

    # --------------------------------------------------------------------
    #  main_view
    # --------------------------------------------------------------------
    def change_api_key_click(e):
        api_key_input.value = load_api_key()
        config_view.visible = True
        main_view.visible = False
        page.update()

    menu = ft.PopupMenuButton(
        icon=ft.Icons.MENU,
        items=[ft.PopupMenuItem(text="Change API key", on_click=change_api_key_click)],
    )

    header = ft.Row(
        controls=[
            ft.Text("DocuPanda", style="headlineMedium"),
            menu,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --------------------------------------------------------------------
    #  UPLOAD: show dialog for dataset name & schema
    # --------------------------------------------------------------------
    dataset_name_field = ft.TextField(label="Dataset Name", width=300)
    schema_dropdown = ft.Dropdown(
        label="Optional: choose a schema",
        options=[],  # Initially empty
        width=300,
    )

    def handle_cancel(dialog, e):
        page.close(dialog)

    def handle_confirm(dialog, e, folder_path, file_count):
        chosen_name = dataset_name_field.value.strip()
        chosen_schema = schema_dropdown.value or None
        page.close(dialog)

        def do_upload():
            show_progress_ui()
            progress_text.value = "Preparing upload..."
            page.update()

            upload_files(
                folder_path,
                load_api_key(),
                chosen_name,
                chosen_schema,
                progress_callback=progress_callback_upload,
                error_callback=handle_upload_error,
            )
            finish_upload()

        threading.Thread(target=do_upload, daemon=True).start()

    def open_folder_dialog(folder_path, file_count):
        dataset_name_field.value = ""
        schema_dropdown.value = ""
        schema_dropdown.options = []  # reset initially
        schema_dropdown.visible = False  # Hide dropdown initially
        page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Settings"),
            content=ft.Column(
                controls=[
                    ft.Text(f"Folder selected: {folder_path}\nDetected {file_count} files."),
                    ft.Text("Please provide a dataset name (required):"),
                    dataset_name_field,
                    ft.Text("Optionally, standardize each document with a schema below:"),
                    schema_dropdown,
                    ft.ProgressRing(visible=True),  # indicator while fetching
                ],
                spacing=10,
            ),
            actions_alignment=ft.MainAxisAlignment.END,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: handle_cancel(dlg, e)),
                ft.ElevatedButton("Confirm Upload", on_click=lambda e: handle_confirm(dlg, e, folder_path, file_count)),
            ],
        )
        page.open(dlg)

        # Fetch schemas dynamically here:
        def fetch_schemas():
            latest_key = get_latest_api_key()
            schemas_fetched = list_schemas(latest_key)
            schema_dropdown.options = [
                ft.dropdown.Option(key=s.schemaId, text=s.schemaName) for s in schemas_fetched
            ]
            schema_dropdown.visible = True  # make dropdown visible after fetching
            dlg.content.controls.pop()  # remove spinner
            page.update()

        threading.Thread(target=fetch_schemas, daemon=True).start()

    def pick_folder_result(e: ft.FilePickerResultEvent):
        if e.path:
            folder_path = Path(e.path)
            all_files = list(folder_path.glob("*"))
            file_count = len([f for f in all_files if f.is_file() and not f.name.startswith(".")])
            open_folder_dialog(folder_path, file_count)
        else:
            show_snackbar("No folder selected.")

    upload_button = ft.ElevatedButton(
        text="Upload Dataset",
        on_click=lambda e: file_picker.get_directory_path()
    )

    # --------------------------------------------------------------------
    #  DOWNLOAD flow
    # --------------------------------------------------------------------
    chosen_folder_path = None
    folder_text_field = ft.TextField(label="Selected Folder", width=400, read_only=True, visible=False)
    dataset_dropdown = ft.Dropdown(
        label="Select a dataset to download",
        options=[],
        width=400,
    )

    def download_folder_result(e: ft.FilePickerResultEvent):
        nonlocal chosen_folder_path
        if e.path:
            chosen_folder_path = Path(e.path)
            folder_text_field.value = str(chosen_folder_path)
            folder_text_field.visible = True
            page.update()
        else:
            show_snackbar("No folder selected.")

    download_folder_picker = ft.FilePicker(on_result=download_folder_result)
    page.overlay.append(download_folder_picker)

    def select_target_directory_click(e):
        download_folder_picker.get_directory_path()

    def handle_download_confirm(dialog, e):
        selected_dataset = dataset_dropdown.value
        if not selected_dataset:
            show_snackbar("Please select a dataset name.")
            return
        if not chosen_folder_path:
            show_snackbar("Please select a target directory.")
            return

        page.close(dialog)

        def do_download():
            show_progress_ui()
            progress_text.value = "Preparing download..."
            page.update()

            download_dataset(
                api_key=get_latest_api_key(),
                dataset_name=selected_dataset,
                output_dir=chosen_folder_path,
                progress_callback=progress_callback_download,
                error_callback=handle_download_error
            )
            finish_download()

        threading.Thread(target=do_download, daemon=True).start()

    def handle_download_cancel(dialog, e):
        page.close(dialog)

    def open_download_dialog(e):
        dataset_names = list_dataset_names(get_latest_api_key())
        dataset_dropdown.options = [ft.dropdown.Option(name, name) for name in dataset_names]
        dataset_dropdown.value = ""
        folder_text_field.value = ""
        nonlocal chosen_folder_path
        chosen_folder_path = None  # reset

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Download Dataset"),
            content=ft.Column(
                width=400,
                controls=[
                    dataset_dropdown,
                    ft.ElevatedButton("Select Target Directory", on_click=select_target_directory_click),
                    folder_text_field,
                ],
                spacing=20,
            ),
            actions_alignment=ft.MainAxisAlignment.END,
            actions=[
                ft.TextButton("Cancel", on_click=lambda ev: handle_download_cancel(dlg, ev)),
                ft.ElevatedButton("Confirm Download", on_click=lambda ev: handle_download_confirm(dlg, ev)),
            ],
        )
        page.open(dlg)

    download_button = ft.ElevatedButton(
        text="Download Dataset Results",
        on_click=open_download_dialog
    )

    file_picker = ft.FilePicker(on_result=pick_folder_result)
    page.overlay.append(file_picker)

    # --------------------------------------------------------------------
    #  MAIN LAYOUT
    # --------------------------------------------------------------------
    buttons_row = ft.Row(
        controls=[upload_button, download_button],
        spacing=20,
    )

    main_view = ft.Column(
        controls=[
            header,
            buttons_row,
            loading_indicator,
            progress_bar,
            progress_text,
        ],
        alignment="center",
        visible=False,
    )

    # --------------------------------------------------------------------
    #  Toggle between config and main
    # --------------------------------------------------------------------
    def show_main_view():
        current_key = get_latest_api_key()
        if current_key:
            config_view.visible = False
            main_view.visible = True
        else:
            config_view.visible = True
            main_view.visible = False
        page.update()

    if load_api_key():
        show_main_view()
    else:
        config_view.visible = True

    page.add(config_view, main_view)


# IMPORTANT: Provide both assets_dir and icon to ensure the icon is visible.
ft.app(
    target=main,

)
