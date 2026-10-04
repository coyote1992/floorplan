"""Selects the flat to build. Every script does `from plan import ...`; the data comes from
blender/flats/<FLAT>.py, chosen with the FLAT environment variable (default: riverview).

Plan conventions shared by all flats: geometry in plan units (px of the source drawing, or cm),
x grows east, y grows south. Blender world: X = east, Y = north, Z = up, metres.
glTF / three.js: x = east, y = up, z = south."""
import importlib
import os

FLAT = os.environ.get('FLAT', 'riverview')
_flat = importlib.import_module('flats.' + FLAT)
globals().update({k: v for k, v in vars(_flat).items() if not k.startswith('__')})
