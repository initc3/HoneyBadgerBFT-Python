import sys
sys.path.append('../../../crypto')

import importlib
from python_encryption_helper import PythonEncryptionHelper
from threshenc.tpke import dealer, encrypt, decrypt

encttypes = importlib.import_module("threshenc.thrift.gen-py.encryption.ttypes")


class PythonEncryptionHandler(PythonEncryptionHelper):
    def __init__(self):
        PythonEncryptionHelper.__init__(self)

    def lagrange(self, tpke_pub_key_thrift_info, S, j):
        tpke_pub_key = \
            self.tpke_pub_key_from_thrift(
                tpke_pub_key_thrift_info=tpke_pub_key_thrift_info,
            )
        return tpke_pub_key.lagrange(S, j)

    def dealer(self, players, k):
        public_key, private_keys = dealer(
            players=players,
            k=k
        )
        return encttypes.DealerThrift(
            PubKey=self.tpke_pub_key_to_thrift(
                tpke_pub_key=public_key
            ),
            PrivKeys=[self.tpke_priv_key_to_thrift(priv_key) for priv_key in private_keys]
        )

    def encrypt(self, tpke_pub_key_thrift_info, m):
        """
        Encrypt a 32 byte message.

        :return: (U,V,W)
        """
        tpke_pub_key = \
            self.tpke_pub_key_from_thrift(
                tpke_pub_key_thrift_info=tpke_pub_key_thrift_info,
            )
        (U, V, W) = tpke_pub_key.encrypt(m)
        return self.encryptedMessageToThrift(
            U=U,
            V=V,
            W=W
        )

    def combineShares(self, tpke_pub_key_thrift_info, em, shares):
        """
        Combine shares
        tpke_pub_key_thrift_info: Public Key
        em: Encrypted message
        shares: map<i32, binary> shares

        :rtype: binary
        """
        tpke_pub_key = \
            self.tpke_pub_key_from_thrift(
                tpke_pub_key_thrift_info=tpke_pub_key_thrift_info,
            )
        U, V, W = self.encryptedMessageFromThrift(enc_msg_thrift_info=em)
        return self.verification_key_to_thrift(
            tpke_pub_key.combine_shares(
                U=U,
                V=V,
                W=W,
                shares=self.shares_from_thrift(shares=shares)
            )
        )

    def decryptShare(self, tpke_priv_key_thrift_info, em):
        tpke_priv_key = \
            self.tpke_priv_key_from_thrift(
                tpke_priv_key_thrift_info=tpke_priv_key_thrift_info
            )
        U, V, W = self.encryptedMessageFromThrift(enc_msg_thrift_info=em)
        return self.verification_key_to_thrift(
            tpke_priv_key.decrypt_share(U, V, W)
        )

    def aesEncrypt(self, key, raw):
        """AES Encrypt
        key: public key
        raw: message to be encrypted

        :return: encrypted binary bytes
        """
        pub_key = self.aes_key_from_thrift(
            aes_key_thrift_info=key
        )
        message = self.aes_key_from_thrift(
            aes_key_thrift_info=raw
        )
        return self.aes_key_to_thrift(
            aes_key=encrypt(key=pub_key, raw=message)
        )

    def aesDecrypt(self, key, enc):
        """AES Decrypt
        key: private key
        raw: message to be decrypted

        :return: decrypted binary bytes
        """
        priv_key = self.aes_key_from_thrift(
            aes_key_thrift_info=key
        )
        encrypted_message = self.aes_key_from_thrift(
            aes_key_thrift_info=enc
        )
        return self.aes_key_to_thrift(
            aes_key=decrypt(key=priv_key, enc=encrypted_message)
        )
