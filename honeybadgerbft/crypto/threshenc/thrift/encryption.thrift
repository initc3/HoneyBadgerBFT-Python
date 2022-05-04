namespace py encryption
namespace go encryption

struct VerificationKeyThrift {
    1: required binary key
}

struct PrivateKeyThrift {
    1: required binary key
}

struct EncryptedMessageThrift {
    1: required binary U,
    2: required binary V,
    3: required binary W
}

struct TPKEPublicKeyThrift {
    1: required i32 l,
    2: required i32 k,
    3: required VerificationKeyThrift VK,
    4: required list<VerificationKeyThrift> VKs,
}

struct TPKEPrivateKeyThrift {
    1: required TPKEPublicKeyThrift PubKey,
    2: required PrivateKeyThrift SK,
    3: required i32 i
}

struct DealerThrift {
    1: required TPKEPublicKeyThrift PubKey,
    2: required list<TPKEPrivateKeyThrift> PrivKeys
}

struct AESKey {
    1: required binary key
}

service TPKEService {
    i32 lagrange(
        1: TPKEPublicKeyThrift PubKey, 
        2: set<i32> S, 
        3: i32 j
    ),
    EncryptedMessageThrift encrypt(
        1: TPKEPublicKeyThrift PubKey, 
        2: string m
    ),
    binary combineShares(
        1: TPKEPublicKeyThrift PubKey, 
        2: EncryptedMessageThrift em, 
        3: map<i32, binary> shares
    ),
    binary decryptShare(
        1: TPKEPrivateKeyThrift PrivKey,
        2: EncryptedMessageThrift em
    ),
    DealerThrift dealer(
        1: i32 players,
        2: i32 k
    ),
    binary aesEncrypt(
        1: AESKey key,
        2: binary raw
    ),
    binary aesDecrypt(
        1: AESKey key,
        2: binary encMes
    )
}

