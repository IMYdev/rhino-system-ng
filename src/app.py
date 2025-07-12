import flet as ft
import asyncio
import os
import re
import errno
import signal
import tempfile
from utils.deviceinfo import DeviceInfo

# Adwaita Dark Theme Colors (Don't ask how I got them, involves soul selling to some cosmic entities)
ADW_BACKGROUND = "#241f31"
ADW_VIEW_BACKGROUND = "#353141"
ADW_TEXT_COLOR = ft.Colors.WHITE
ADW_SECONDARY_TEXT_COLOR = ft.Colors.GREY_400
ADW_BORDER_COLOR = ADW_BACKGROUND
BUTTON_BG_COLOR = "#372b50"
BUTTON_TEXT_COLOR = "#d28dff"
BUTTON_SECONDARY_BG_COLOR = "#9235ff"

def build_ui(page: ft.Page):
    page.window.height = 760
    page.window.width = 580
    page.title = "Your System"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ADW_BACKGROUND
    page.padding = 0


    sudo_password_field = ft.TextField(
        label="Sudo Password",
        password=True,
        can_reveal_password=True,
        autofocus=True,
        width=300
    )

    log_column = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=4, expand=True, auto_scroll=True)

    log_view = ft.Container(
        content=log_column,
        width=page.width * 0.75,
        height=400,
        padding=10,
        bgcolor=ft.Colors.BLACK,
        border_radius=ft.border_radius.all(8),
        clip_behavior=ft.ClipBehavior.HARD_EDGE
        )


    output_dialog = ft.AlertDialog(
        modal=True,
        content=log_view,
        bgcolor=ft.Colors.BLACK,
        shape=ft.BeveledRectangleBorder(),
        actions=[ft.TextButton("Cancel", on_click=lambda e: cancel_upgrade())],
        scrollable=True
    )
    page.overlay.append(output_dialog)

    def show_output_dialog():
        log_column.controls.clear()
        output_dialog.open = True
        page.update()

    def close_output_dialog():
        output_dialog.open = False
        page.update()

    password_dialog = ft.AlertDialog(
        modal=True,
        content=sudo_password_field,
        bgcolor=ADW_BACKGROUND,
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: close_password_dialog()),
            ft.Button("Continue", bgcolor=ADW_VIEW_BACKGROUND, color=ADW_TEXT_COLOR, on_click=lambda e: asyncio.run(on_password_submit()))
        ]
    )

    page.overlay.append(password_dialog)

    def close_password_dialog():
        password_dialog.open = False
        sudo_password_field.value = ""
        page.update()

    async def on_password_submit():
        password = sudo_password_field.value + "\n"
        close_password_dialog()
        show_output_dialog()
        await run_upgrade(password)


    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

    def clean_log_line(line):
        return ansi_escape.sub('', line).strip()
    
    running_processes = {}
    async def run_upgrade(password):
        try:
            log_column.controls.append(ft.Text("Upgrading system...", color=ft.Colors.BLUE_200))
            output_dialog.open = True
            output_dialog.update()
            # Write a temporary expect script
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".expect") as tmp:
                tmp.write(f"""#!/usr/bin/expect -f
    log_user 1
    set timeout -1
    spawn rpk update -y
    expect {{
        -re "(?i)password.*:" {{
            send "{password}\\r"
            exp_continue
        }}
        eof
    }}""")
                script_path = tmp.name

            # Make temp script executable
            os.chmod(script_path, 0o700)
            master_fd, slave_fd = os.openpty()

            proc = await asyncio.create_subprocess_exec(
                script_path, password,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid  # Without this, we'd only cancel the application and the update will still be going.
            )
            os.close(slave_fd)
            running_processes["upgrade"] = proc

            while True:
                try:
                    data = await asyncio.get_event_loop().run_in_executor(None, os.read, master_fd, 1024)
                    if not data:
                        break
                except OSError as e:
                    if e.errno == errno.EIO:
                        # This is expected when the child process closes the PTY
                        break
                    else:
                        raise  # Let actual unexpected errors be raised

                text = data.decode(errors="ignore")

                if "try again" in text.lower():
                    log_column.controls.append(ft.Text("Wrong password, close the program.", color=ft.Colors.RED_300, size=10, font_family="monospace"))
                    output_dialog.update()
                    return

                clean_line = clean_log_line(text)
                if clean_line:
                    log_column.controls.append(ft.Text(clean_line, color=ft.Colors.GREEN_100, size=10, font_family="monospace", selectable=True))
                    output_dialog.update()

            await proc.wait()

        except Exception as e:
            log_column.controls.append(ft.Text(f"Error: {e}", color=ft.Colors.RED_400))
        finally:
            output_dialog.update()


    def cancel_upgrade():
        proc = running_processes.get("upgrade")
        if proc:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                log_column.controls.append(ft.Text("Upgrade cancelled by user.", color=ft.Colors.ORANGE_300))
            except ProcessLookupError:
                log_column.controls.append(ft.Text("Process already terminated.", color=ft.Colors.YELLOW_300))
            output_dialog.update()
        else:
            close_output_dialog()




    def create_info_row(title, value):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            border=ft.border.only(bottom=ft.border.BorderSide(1, ADW_BORDER_COLOR)),
            content=ft.Row(
                [
                    ft.Text(f"{title}", size=14),
                    ft.Text(value, size=14, selectable=True, font_family="monospace", color=ADW_SECONDARY_TEXT_COLOR),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

    results_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)

    rhino_logo = ft.Container(
        content=ft.Column(
            controls=[
                ft.Image(src="rhino.png", width=100, height=100),
                ft.Text("Rhino Linux", size=32, weight=ft.FontWeight.BOLD, color=ADW_TEXT_COLOR),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=ft.padding.only(top=10)
    )

    os_version_button = ft.Container(
        content=ft.Button(
            text=DeviceInfo.get_os_version(),
            bgcolor=BUTTON_BG_COLOR,
            color=BUTTON_TEXT_COLOR,
            height=45,
            width=105,
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
            ),
        ),
        padding=ft.padding.only(top=0, bottom=10)
    )

    upgrade_button = ft.Container(
        content=ft.Button(
            text="System Upgrade",
            bgcolor=BUTTON_SECONDARY_BG_COLOR,
            color=ADW_TEXT_COLOR,
            height=45,
            width=170,
            on_click=lambda e: show_password_dialog()
        ),
        margin=ft.margin.only(bottom=page.height / 35) # Cursed I know.
    )

    def show_password_dialog():
        password_dialog.open = True
        page.dialog = password_dialog
        page.update()

    def fetch_data(e=None):
        results_list.controls.clear()
        page.update()

        info_map = {
            "Board": DeviceInfo.get_board_info,
            "Chip": DeviceInfo.get_cpu_info,
            "Memory": DeviceInfo.get_memory_info,
            "Disk": DeviceInfo.get_disk_info,
            "GPU": DeviceInfo.get_gpu_info,
            "Kernel": DeviceInfo.get_kernel_info,
            "Desktop": DeviceInfo.get_desktop_info,
            "Operating System": DeviceInfo.get_os_info,
        }

        for title, func in info_map.items():
            try:
                value = func()
                results_list.controls.append(create_info_row(title, value))
            except Exception as ex:
                results_list.controls.append(create_info_row(title, f"Error: {ex}"))

        page.update()

    list_container = ft.Container(
        content=results_list,
        border=ft.border.all(1, ADW_BORDER_COLOR),
        border_radius=10,
        width=page.width / 2,
        bgcolor=ADW_VIEW_BACKGROUND,
        margin=ft.margin.only(left=35, right=35),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 5),
        ),
    )

    main_layout = ft.Column(
        controls=[
            rhino_logo,
            os_version_button,
            ft.Column(
                controls=[list_container],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            upgrade_button
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(main_layout)
    fetch_data()

    page.on_close = cancel_upgrade