import argparse
import subprocess
import sys
import time
import webbrowser

FRONTENDS = {
    "streamlit": {
        "profile": "streamlit",
        "url": "http://127.0.0.1:8501",
    },
    "react": {
        "profile": "react",
        "url": "http://127.0.0.1:5173",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Start or stop the app through Docker Compose."
    )
    parser.add_argument(
        "--frontend",
        choices=FRONTENDS.keys(),
        default="streamlit",
        help="Choose which frontend to open. Use streamlit or react.",
    )
    parser.add_argument(
        "--down",
        action="store_true",
        help="Stop and remove all Docker Compose containers for this app.",
    )
    return parser.parse_args()


def run_compose(command, action_label):
    print(action_label)
    print(" ".join(command))

    try:
        return subprocess.run(command, check=False).returncode
    except FileNotFoundError:
        print("Docker Compose was not found. Start Docker Desktop and try again.")
        return 1


def start_frontend(frontend_name):
    frontend = FRONTENDS[frontend_name]

    # One launcher command should do the whole job: build if needed, start in
    # the background, and then open the correct browser URL.
    command = [
        "docker",
        "compose",
        "--profile",
        frontend["profile"],
        "up",
        "-d",
        "--build",
    ]

    return_code = run_compose(
        command,
        f"Starting {frontend_name} with Docker Compose...",
    )

    if return_code != 0:
        return return_code

    # Give Streamlit/Vite a short moment to bind to the port before opening.
    time.sleep(3)
    webbrowser.open(frontend["url"])
    print(f"Opened {frontend['url']}")
    return 0


def stop_everything():
    # Include both profiles so Compose also stops optional frontend services.
    command = [
        "docker",
        "compose",
        "--profile",
        "streamlit",
        "--profile",
        "react",
        "down",
    ]
    return run_compose(command, "Stopping all Docker Compose containers...")


def main():
    args = parse_args()
    if args.down:
        return stop_everything()

    return start_frontend(args.frontend)


if __name__ == "__main__":
    sys.exit(main())
