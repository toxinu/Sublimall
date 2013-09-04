#!/usr/bin/env python
"""
CBC Mode of operation

Running this file as __main__ will result in a self-test of the algorithm.

Algorithm per NIST SP 800-38A http://csrc.nist.gov/publications/nistpubs/800-38a/sp800-38a.pdf

Copyright (c) 2010, Adam Newman http://www.caller9.com/
Licensed under the MIT license http://www.opensource.org/licenses/mit-license.php
"""
__author__ = "Adam Newman"

try:
    from aespython.cipher_mode import CipherMode
    from aespython.mode_test import GeneralTestEncryptionMode
except:
    from cipher_mode import CipherMode
    from mode_test import GeneralTestEncryptionMode

class CBCMode(CipherMode):
    """Perform CBC operation on a block and retain IV information for next operation"""
    
    name = "CBC"

    def __init__(self, block_cipher, block_size):
        CipherMode.__init__(self, block_cipher, block_size)        
   
    def encrypt_block(self, plaintext):
        ciphertext = self._block_cipher.cipher_block([i ^ j for i,j in zip (plaintext, self._iv)])
        self._iv = ciphertext
        return ciphertext
    
    def decrypt_block(self, ciphertext):
        result_decipher = self._block_cipher.decipher_block(ciphertext)
        plaintext = [i ^ j for i,j in zip (self._iv, result_decipher)]
        self._iv = ciphertext
        return plaintext

class TestEncryptionMode(GeneralTestEncryptionMode):
    def test_mode(self):
        """Test CBC Mode Encrypt/Decrypt"""        
        try:
            from aespython.test_keys import TestKeys
        except:
            from test_keys import TestKeys
             
        test_data = TestKeys()

        test_mode = CBCMode(self.get_keyed_cipher(test_data.test_mode_key), 16)        
        
        self.run_cipher(test_mode, test_data.test_mode_iv, test_data.test_cbc_ciphertext, test_data.test_mode_plaintext)

if __name__ == "__main__":
    import unittest
    unittest.main()
