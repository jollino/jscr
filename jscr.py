#!/usr/bin/env python3

import os
import shlex
import subprocess
import sys
import time
import tomllib
from threading import Thread

class CameraRecorder:
	def __init__(self, camera_config, main_config):
		self.name = camera_config[0]
		self.config = camera_config[1]
		self.url = f"rtsp://{self.config['username']}:{self.config['password']}@{self.config['hostname']}{self.config['stream']}"
		self.video_duration = int(main_config["video_duration"]) * 60
		self.output_directory = main_config["output_directory"]
		self.process = None

	def _print_update(self, text):
		print(f"[{self.name}] {text}")

	def start_recording(self):
		self._print_update("started recording")
		_cmd = ["sleep", "10"]
		cmd = f"ffmpeg -i '{self.url}' -vcodec copy -acodec aac -map 0 -f segment -segment_time {self.video_duration} -reset_timestamps 1 -strftime 1 -segment_format mp4 '{self.output_directory}/{self.name}-%Y-%m-%d_%H-%M-%S.mp4'"
		args = shlex.split(cmd)
		self._print_update("=> " + str(args))
		self.process = subprocess.Popen(_cmd)
		self._print_update(self.process)

	def is_recording(self):
		if self.process is None:
			self._print_update("not created yet")
			return False
		if self.process.poll() is None:
			self._print_update("is recording")
			return True
		else:
			self._print_update("is not recording")
			return False

	def stop_recording(self):
		self._print_update("stopped recording")
		if self.check_recording():
			self.process.send_signal(2) 	# SIGNINT

	def ensure_recording(self):
		self._print_update("ensuring recording")
		if not self.is_recording():
			self.start_recording()

	def cycle_recording(self):
		self._print_update("cycling")
		if self.check_recording():
			self.stop_recording()
		self.start_recording()



def parse_config():
	if not os.path.isfile("jscr.toml"):
		raise FileNotFoundError("Configuration file jscr.toml is missing, cannot proceed")
	with open("jscr.toml", "rb") as f:
		config = tomllib.load(f)
	
	if "output_directory" not in config["main"]:
		config["main"]["output_directory"] = "." # default
	else:
		if not os.path.isdir(config["main"]["output_directory"]):
			# TBI: create it?
			raise NotADirectoryError(f"Output directory {config['main']['output_directory']} not found")

	if len(config["camera"]) < 1:
		raise SystemError("No cameras defined")
	return config


def main():
	try:
		config = parse_config()
	except Exception as e:
		# {type(e).__name__}
		print(f"Fatal error reading configuration: {e}")
		sys.exit(-1)

	recorders = []
	for camera in config["camera"].items():
		recorder = CameraRecorder(camera, config["main"])
		#recorder.start_recording()
		recorders.append(recorder)

	while True:
		for recorder in recorders:
			recorder.ensure_recording()
		time.sleep(1)

	# 

if __name__ == '__main__':
	main()
