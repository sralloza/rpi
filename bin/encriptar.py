import argparse

from rpi.cifrado import encrypt_file

parser = argparse.ArgumentParser()
parser.add_argument('file', help="archivo a encriptar")

opt = vars(parser.parse_args())

encrypt_file(filename=opt['file'])