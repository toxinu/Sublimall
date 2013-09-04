# -*- coding:utf-8 -*-
import os
import sys
import struct
import hashlib
from io import BytesIO

sys.path.append(os.path.dirname(__file__))
from aespython import key_expander, aes_cipher, cbc_mode


class Crypto(object):
    def __init__(self, stream):
        self.stream = stream
        self._iv = None
        self._key = None
        self._salt = None
        self.out_stream = None

    def new_salt(self):
        self._salt = os.urandom(32)

    def set_iv(self, iv):
        self._iv = iv

    def create_key_from_password(self, password):
        if self._salt is None:
            return
        sha512 = hashlib.sha512(password.encode('utf-8') + self._salt[:16]).digest()
        self._key = bytearray(sha512[:32])
        self._iv = [i ^ j for i, j in zip(bytearray(self._salt[16:]), bytearray(sha512[32:48]))]

    def encrypt_data(self, password=None):
        """
        Encrypt stream data
        """
        if password is not None:
            self.new_salt()
            self.create_key_from_password(password)
        else:
            self._salt = None

        #If key and iv are not provided are established above, bail out.
        if self._key is None or self._iv is None:
            return False

        #Initialize encryption using key and iv
        key_expander_256 = key_expander.KeyExpander(256)
        expanded_key = key_expander_256.expand(self._key)
        aes_cipher_256 = aes_cipher.AESCipher(expanded_key)
        aes_cbc_256 = cbc_mode.CBCMode(aes_cipher_256, 16)
        aes_cbc_256.set_iv(self._iv)

        #Get filesize of original file for storage in encrypted file
        try:
            self.stream.seek(0,2)
            filesize = self.stream.tell()
            print(filesize)
        except Exception:
            return False

        out_stream = BytesIO()
        self.stream.seek(0)

        #Write salt if present
        if self._salt is not None:
            out_stream.write(self._salt)

        #Write filesize of original
        out_stream.write(struct.pack('L',filesize))

        #Encrypt to eof
        eof = False
        while not eof:
            in_data = self.stream.read(16)
            if len(in_data) == 0:
                eof = True
            else:
                out_data = aes_cbc_256.encrypt_block(bytearray(in_data))
                out_stream.write(bytes(out_data))

        self._salt = None
        out_stream.seek(0)
        return out_stream

    def decrypt_data(self, password=None):
        """
        Decrypts data
        """
        self.stream.seek(0)

        # Get salt from file
        if password is not None:
            self._salt = self.stream.read(32)
            self.create_key_from_password(password)

        if self._key is None or self._iv is None:
            return False

        key_expander_256 = key_expander.KeyExpander(256)
        expanded_key = key_expander_256.expand(self._key)
        aes_cipher_256 = aes_cipher.AESCipher(expanded_key)
        aes_cbc_256 = cbc_mode.CBCMode(aes_cipher_256, 16)
        aes_cbc_256.set_iv(self._iv)

        filesize = struct.unpack('L',self.stream.read(struct.calcsize('L')))[0]
        out_stream = BytesIO()

        eof = False
        while not eof:
            in_data = self.stream.read(16)
            if len(in_data) == 0:
                eof = True
            else:
                out_data = aes_cbc_256.decrypt_block(list(bytearray(in_data)))
                #At end of file, if end of original file is within < 16 bytes slice it out.
                if filesize - out_stream.tell() < 16:
                    out_stream.write(bytes(out_data[:filesize - out_stream.tell()]))
                else:
                    out_stream.write(bytes(out_data))


        self._salt = None
        return out_stream