import argparse

from rpi.cifrado import decrypt_file

parser = argparse.ArgumentParser()
parser.add_argument('file', help="archivo a desencriptar")

opt = vars(parser.parse_args())

decrypt_file(filename=opt['file'])
