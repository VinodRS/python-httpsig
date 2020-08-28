import base64

import six
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from httpsig.utils import HttpSigException, HASHES
from abc import ABCMeta, abstractmethod

DEFAULT_HASH_ALGORITHM = "sha512"


class SignAlgorithm(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def sign(self, private, data):
        raise NotImplementedError()

    @abstractmethod
    def verify(self, public, data, signature):
        raise NotImplementedError()


class PSS(SignAlgorithm):

    def __init__(self, hash_algorithm=DEFAULT_HASH_ALGORITHM, salt_length=None, mgfunc=None):
        if hash_algorithm not in HASHES:
            raise HttpSigException("Unsupported hash algorithm")

        if hash_algorithm != DEFAULT_HASH_ALGORITHM:
            raise HttpSigException(
                "Hash algorithm: {} is deprecated. Please use: {}".format(hash_algorithm, DEFAULT_HASH_ALGORITHM))

        self.hash_algorithm = HASHES[hash_algorithm]
        self.salt_length = salt_length
        self.mgfunc = mgfunc

    def _create_pss(self, key, salt_length):
        try:
            rsa_key = RSA.importKey(key)
            pss = PKCS1_PSS.new(rsa_key, saltLen=salt_length, mgfunc=self.mgfunc)
        except ValueError:
            raise HttpSigException("Invalid key.")
        return pss

    def sign(self, private_key, data):
        if isinstance(data, six.string_types):
            data = data.encode("ascii")

        h = self.hash_algorithm.new()
        h.update(data)

        salt_length = self.salt_length
        if salt_length is None:
            salt_length = h.digest_size

        pss = self._create_pss(private_key, salt_length)

        return pss.sign(h)

    def verify(self, public_key, data, signature):
        h = self.hash_algorithm.new()
        h.update(data)

        salt_length = self.salt_length
        if salt_length is None:
            salt_length = h.digest_size

        pss = self._create_pss(public_key, salt_length)

        return pss.verify(h, base64.b64decode(signature))
