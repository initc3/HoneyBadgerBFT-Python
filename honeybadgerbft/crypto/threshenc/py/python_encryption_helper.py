"""Helper file to convert to and from thrift."""
import sys
import importlib
from charm.toolbox.pairinggroup import PairingGroup
from base64 import encodestring, decodestring

sys.path.append('../../../crypto')


from threshenc.tpke import TPKEPublicKey, TPKEPrivateKey

encttypes = importlib.import_module("threshenc.thrift.gen-py.encryption.ttypes")
group = PairingGroup('SS512')


class PythonEncryptionHelper(object):
    def __init__(self):
        self.initialize = True

    def verification_key_from_thrift(self, ver_key_thrift_info):
        return group.deserialize(encodestring(ver_key_thrift_info.key))

    def verification_key_to_thrift(self, ver_key):
        return encttypes.VerificationKeyThrift(
            key=decodestring(group.serialize(ver_key))
        )

    def aes_key_from_thrift(self, aes_key_thrift_info):
        return decodestring(aes_key_thrift_info)

    def aes_key_to_thrift(self, aes_key):
        return encodestring(aes_key)

    def tpke_pub_key_from_thrift(self, tpke_pub_key_thrift_info):
        return TPKEPublicKey(
            l=tpke_pub_key_thrift_info.l,
            k=tpke_pub_key_thrift_info.k,
            VK=self.verification_key_from_thrift(tpke_pub_key_thrift_info.VK),
            VKs=[self.verification_key_from_thrift(x) for x in
                 tpke_pub_key_thrift_info.VKs]
        )

    def tpke_pub_key_to_thrift(self, tpke_pub_key):
        return encttypes.TPKEPublicKeyThrift(
            l=tpke_pub_key.l,
            k=tpke_pub_key.k,
            VK=self.verification_key_to_thrift(tpke_pub_key.VK),
            VKs=[self.verification_key_to_thrift(x) for x in
                 tpke_pub_key.VKs]
        )

    def tpke_priv_key_from_thrift(self, tpke_priv_key_thrift_info):
        return TPKEPrivateKey(
            l=tpke_priv_key_thrift_info.PubKey.l,
            k=tpke_priv_key_thrift_info.PubKey.k,
            VK=self.verification_key_from_thrift(tpke_priv_key_thrift_info.PubKey.VK),
            VKs=[self.verification_key_from_thrift(x) for x in
                 tpke_priv_key_thrift_info.PubKey.VKs],
            SK=self.verification_key_from_thrift(tpke_priv_key_thrift_info.SK),
            i=tpke_priv_key_thrift_info.i
        )

    def tpke_priv_key_to_thrift(self, tpke_priv_key):
        return encttypes.TPKEPrivateKeyThrift(
            PubKey=self.tpke_pub_key_to_thrift(
                tpke_pub_key=TPKEPublicKey(
                    l=tpke_priv_key.l,
                    k=tpke_priv_key.k,
                    VK=tpke_priv_key.VK,
                    VKs=tpke_priv_key.VKs
                )
            ),
            SK=self.verification_key_to_thrift(tpke_priv_key.SK),
            i=tpke_priv_key.i
        )

    def encryptedMessageFromThrift(self, enc_msg_thrift_info):
        U = self.verification_key_from_thrift(enc_msg_thrift_info.U)
        V = decodestring(enc_msg_thrift_info.V)
        W = self.verification_key_from_thrift(enc_msg_thrift_info.W)
        return U, V, W

    def encryptedMessageToThrift(self, U, V, W):
        UThrift = self.verification_key_to_thrift(U)
        VThrift = encodestring(V)
        WThrift = self.verification_key_to_thrift(W)
        return encttypes.EncryptedMessageThrift(
            U=UThrift,
            V=VThrift,
            W=WThrift
        )

    def shares_from_thrift(self, shares):
        shares_dict = {}
        for idx, share in shares.items():
            shares_dict[idx] = self.verification_key_from_thrift(share)
        return shares_dict

    def shares_to_thrift(self, shares):
        shares_dict = {}
        for idx, share in shares.items():
            shares_dict[idx] = self.verification_key_to_thrift(share)
        return shares_dict
