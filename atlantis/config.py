import argparse
import os
import logging


class Config:
    def __init__(self, output_path: str, enable_render: bool):
        self.output_path = output_path
        self.enable_render = enable_render

    @classmethod
    def initialize(
        cls,
        default_log_file="atlantis.log",
        default_log_level=logging.INFO,
        default_enable_render=False,
    ):
        parser = argparse.ArgumentParser(
            description="Script to run Atlantis Pearl Processing simulator"
        )
        parser.add_argument("--output-path", default="out")
        parser.add_argument("--log-level", default=default_log_level)
        parser.add_argument(
            "--enable-render", default=default_enable_render, action="store_true"
        )

        args = parser.parse_args()

        # Ensure output path
        base_dir = os.path.abspath(os.path.dirname(f"./{args.output_path}/"))
        os.makedirs(base_dir, exist_ok=True)

        logging.basicConfig(
            level=args.log_level,
            format="[%(asctime)s] %(levelname)s: [%(name)s]: %(message)s",
            datefmt="%H:%M:%S",
            handlers=[
                logging.FileHandler(f"./{args.output_path}/{default_log_file}", "w"),
                logging.StreamHandler(),
            ],
        )
        return cls(args.output_path, args.enable_render)
