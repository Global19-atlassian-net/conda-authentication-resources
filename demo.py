# -*- coding: utf-8 -*-

import os
import json

import car.metadata_construction
import car.common
import car.signing
import car.root_signing
import car.authentication


PRESENT_SLOWLY = True

ROOT_PUBKEY_HEX = 'bfbeb6554fca9558da7aa05c5e9952b7a1aa3995dede93f3bb89f0abecc7dc07'
ROOT_PUBKEY_GPG_FINGERPRINT = 'f075dd2f6f4cb3bd76134bbb81b6ca16ef9cd589'

ROOT_PUBKEY_2_HEX = 'd16d07f038e49de3b3bd8661523ef0948181e3109902a9c739beeb69628940c4'
ROOT_PUBKEY_2_GPG_FINGERPRINT = '39561c2c63b681a60147c1685dcd89e98d05d0dd'

KEYMGR_PRIVATE_HEX = 'c9c2060d7e0d93616c2654840b4983d00221d8b6b69c850107da74b42168f937'
KEYMGR_PUBLIC_HEX = '013ddd714962866d12ba5bae273f14d48c89cf0773dee2dbf6d4561e521c83f7'

PKGMGR_PUBLIC_HEX = 'f46b5a7caa43640744186564c098955147daa8bac4443887bc64d8bfee3d3569'
PKGMGR_PRIVATE_HEX = 'f3cdab14740066fb277651ec4f96b9f6c3e3eb3f812269797b9656074cd52133'

ROOT_FNAME_V1 = 'demo/1.root.json' # Note that this will be overwritten.
ROOT_FNAME_V2 = 'demo/2.root.json' # Note that this will be overwritten.

KEYMGR_FNAME = 'demo/key_mgr.json' # Note that this will be overwritten.

# In Python2, input() performs evaluation and raw_input() does not.  In
# Python3, input() does not perform evaluation and there is no raw_input().
# So... use raw_input in Python2, and input in Python3.
try:
    _input_func = raw_input
except NameError:
    _input_func = input

# Step by step demo or an uninterrupted run, based on PRESENT_SLOWLY.
def input_func(s):
    if PRESENT_SLOWLY:
        return _input_func(s)
    else:
        return print(s)


def main():

    junk = input_func(
            '\n\n\n\nFirst: a demo of root metadata creation, verification, '
            'updating, and root chaining -- verifying a new untrusted version '
            'of root metadata using the prior, trusted version of root '
            'metadata.\n')
    root_v1, root_v2 = demo_root_signing_and_verifying_and_chaining()

    # This one uses existing files, if preferred, and just does the chaining
    # test.
    # demo_root_chaining(root_v1, root_v2) # redundant test for my dev purposes

    # To load metadata from a file
    # key_mgr = car.common.load_metadata_from_file('test_key_mgr.json')

    # If loading a key from file, for example....
    # with open(name + '.pri', 'rb') as fobj:
    #         private_bytes = fobj.read()


    junk = input_func(
            '\n\n\nSecond: a demo of the creation and signing of the key '
            'manager role (key_mgr.json), a role root delegates to.')
    key_mgr = demo_create_and_sign_key_mgr()


    junk = input_func(
            '\n\n\nThird: a demo of the verification of the key manager '
            'metadata using trusted root metadata.')
    demo_verify_key_mgr_using_root(key_mgr, root_v2)


    junk = input_func(
            '\n\n\nFourth: a demo of verification of an individual package '
            'signature using the now-trusted key manager metadata.')
    demo_verify_pkg_sig_via_key_mgr(key_mgr)




def demo_create_and_sign_key_mgr():

    prikey_keymgr = car.common.PrivateKey.from_hex(KEYMGR_PRIVATE_HEX)
    # pubkey_keymgr = car.common.PublicKey.from_bytes(KEYMGR_PUBLIC_BYTES)
    # print('public test key for keymgr: ' + pubkey_keymgr.to_hex())
    # print('private test key for keymgr: ' + prikey_keymgr.to_hex())

    key_mgr = car.metadata_construction.build_delegating_metadata(
            metadata_type='intermediate', # 'root' or 'intermediate'
            delegations={'pkg_mgr.json': {
                'pubkeys': [PKGMGR_PUBLIC_HEX],
                'threshold': 1}},
            version=1,
            #timestamp   default: now
            #expiration  default: now plus root expiration default duration
            )

    key_mgr = car.signing.wrap_as_signable(key_mgr)

    # sign dictionary in place
    car.signing.sign_signable(key_mgr, prikey_keymgr)

    with open(KEYMGR_FNAME, 'wb') as fobj:
        fobj.write(car.common.canonserialize(key_mgr))

    return key_mgr





def demo_verify_key_mgr_using_root(key_mgr_metadata, root_metadata):

    # Some argument validation
    car.common.checkformat_signable(root_metadata)
    if 'delegations' not in root_metadata['signed']:
        raise ValueError('Expected "delegations" entry in root metadata.')
    root_delegations = root_metadata['signed']['delegations'] # for brevity
    car.common.checkformat_delegations(root_delegations)
    if 'key_mgr.json' not in root_delegations:
        raise ValueError(
                'Expected delegation to "key_mgr.json" in root metadata.')
    car.common.checkformat_delegation(
            root_delegations['key_mgr.json'])


    # Doing delegation processing.
    car.authentication.verify_delegation(
            'key_mgr.json', key_mgr_metadata, root_metadata)

    print('\n-- Success: key mgr metadata verified based on root metadata.')



def demo_root_signing_and_verifying_and_chaining():
    # Build sample root metadata.  ('metadata' -> 'md')
    root_md = car.metadata_construction.build_root_metadata(
            root_pubkeys=[ROOT_PUBKEY_HEX],
            root_threshold=1,
            root_version=1,
            key_mgr_pubkeys=[KEYMGR_PUBLIC_HEX],
            key_mgr_threshold=1)

    # Wrap the metadata in a signing envelope.
    root_md = car.signing.wrap_as_signable(root_md)

    root_md_serialized_unsigned = car.common.canonserialize(root_md)

    print('\n-- Unsigned root metadata version 1 generated.\n')

    # # This is the part of the data over which signatures are constructed.
    # root_md_serialized_portion_to_sign = car.common.canonserialize(
    #         root_md['signed'])


    # TODO: ✅ Format-validate constructed root metadata using checkformat
    #          function.

    if not os.path.exists('demo'):
        os.mkdir('demo')

    # Write unsigned sample root metadata.
    with open(ROOT_FNAME_V1, 'wb') as fobj:
        fobj.write(root_md_serialized_unsigned)
    print('\n-- Unsigned root metadata version 1 written.\n')


    # Sign sample root metadata.
    junk = input_func(
            'Preparing to request root signature.  Please plug in your '
            'YubiKey and prepare to put in your user PIN in a GPG dialog box. '
            ' When the YubiKey is plugged in and you are READY TO ENTER your '
            'pin, hit enter to begin.')

    # This overwrites the file with a signed version of the file.
    car.root_signing.sign_root_metadata_via_gpg(
            ROOT_FNAME_V1, ROOT_PUBKEY_GPG_FINGERPRINT)
    car.root_signing.sign_root_metadata_via_gpg(
            ROOT_FNAME_V1, ROOT_PUBKEY_GPG_FINGERPRINT)
    junk = input_func('\n-- Root metadata v1 signed.  Next: load signed root v1.\n')


    # Load untrusted signed root metadata.
    signed_root_md = car.common.load_metadata_from_file(ROOT_FNAME_V1)
    junk = input_func('\n-- Signed root metadata v1 loaded.  Next: verify signed root v1\n')

    # Verify untrusted signed root metadata.  (Normally, one uses the prior
    # version of root, but here we're bootstrapping for the demo.  We'll verify
    # with a prior version lower down in this demo.)
    car.authentication.verify_signable(
            signed_root_md, [ROOT_PUBKEY_HEX], 1, gpg=True)
    junk = input_func('\n-- Root metadata v1 fully verified.  Next: build root metadata v2.\n')


    # Build sample second version of root metadata.
    root_md2 = car.metadata_construction.build_root_metadata(
            root_pubkeys=[ROOT_PUBKEY_HEX],
            root_threshold=1,
            root_version=2,
            key_mgr_pubkeys=[KEYMGR_PUBLIC_HEX],
            key_mgr_threshold=1)

    # Wrap the version 2 metadata in a signing envelope, canonicalize it, and
    # serialize it to write to disk.
    root_md2 = car.signing.wrap_as_signable(root_md2)
    root_md2 = car.common.canonserialize(root_md2)


    # Write unsigned sample root metadata.
    with open(ROOT_FNAME_V2, 'wb') as fobj:
        fobj.write(root_md2)
    junk = input_func('\n-- Unsigned root metadata version 2 generated and written.  Next: sign root v2\n')

    # This overwrites the file with a signed version of the file.
    car.root_signing.sign_root_metadata_via_gpg(
            ROOT_FNAME_V2, ROOT_PUBKEY_GPG_FINGERPRINT)
    car.root_signing.sign_root_metadata_via_gpg(
            ROOT_FNAME_V2, ROOT_PUBKEY_2_GPG_FINGERPRINT)
    junk = input_func('\n-- Root metadata v2 signed.  Next: load and verify signed root v2 based on root v1 (root chaining).\n')

    # Load the now-signed version from disk.
    signed_root_md2 = car.common.load_metadata_from_file(ROOT_FNAME_V2)

    # Test root chaining (verifying v2 using v1)
    car.authentication.verify_root(signed_root_md, signed_root_md2)
    print(
            '\n-- Root metadata v2 fully verified based directly on Root '
            'metadata v1 (root chaining success)\n')

    print('\n-- Success. :)\n')

    return signed_root_md, signed_root_md2



def demo_root_chaining_w_files(trusted_root_fname, new_untrusted_root_fname):
    # Just does the chaining part from
    # demo_root_signing_and_verifying_and_chaining, but using metadata files
    # instead of metadata dictionaries.

    # TODO: Contemplate the safest way to hold this metadata in conda during
    #       execution.  I gather that much of what conda does with env
    #       variables, for example, can be compromised by random packages
    #       adding environment variables?

    trusted_root = car.common.load_metadata_from_file(trusted_root_fname)

    untrusted_root = car.common.load_metadata_from_file(new_untrusted_root_fname)

    # Use that to verify the next root.

    verify_root(trusted_root, untrusted_root)




def demo_verify_pkg_sig_via_key_mgr(key_mgr):

    packages = {
        "pytorch-1.2.0-cuda92py27hd3e106c_0.tar.bz2": {
              "build": "cuda92py27hd3e106c_0",
              "build_number": 0,
              "depends": [
                "_pytorch_select 0.2",
                "blas 1.0 mkl",
                "cffi",
                "cudatoolkit 9.2.*",
                "cudnn >=7.3.0,<=8.0a0",
                "future",
                "libgcc-ng >=7.3.0",
                "libstdcxx-ng >=7.3.0",
                "mkl >=2019.4,<2021.0a0",
                "mkl-service >=2,<3.0a0",
                "ninja",
                "numpy >=1.11.3,<2.0a0",
                "python >=2.7,<2.8.0a0"
              ],
              "license": "BSD 3-Clause",
              "license_family": "BSD",
              "md5": "793c6af90ed62c964e28b046e0b071c6",
              "name": "pytorch",
              "sha256": "a53f772a224485df7436d4b2aa2c5d44e249e2fb43eee98831eeaaa51a845697",
              "size": 282176733,
              "subdir": "linux-64",
              "timestamp": 1566783471689,
              "version": "1.2.0"
        }}


    print('\n\n\nHere is a sample package entry from repodata.json:')
    from pprint import pprint
    pprint(packages)
    junk = input_func('\n\nNext: sign it with the pkg_mgr key.')

    signable = car.signing.wrap_as_signable(
            packages['pytorch-1.2.0-cuda92py27hd3e106c_0.tar.bz2'])

    # Sign in place.
    car.signing.sign_signable(
            signable,
            car.common.PrivateKey.from_hex('f3cdab14740066fb277651ec4f96b9f6c3e3eb3f812269797b9656074cd52133'))

    print('Signed envelope around this pytorch package metadata:\n\n')
    pprint(signable)

    junk = input_func(
            '\n\nNext: verify the signature based on what the now-trusted '
            'key manager role told us to expect.\n')



    # Some argument validation for the key manager role.
    car.common.checkformat_signable(key_mgr)
    if 'delegations' not in key_mgr['signed']:
        raise ValueError('Expected "delegations" entry in key manager metadata.')
    key_mgr_delegations = key_mgr['signed']['delegations'] # for brevity
    car.common.checkformat_delegations(key_mgr_delegations)
    if 'pkg_mgr.json' not in key_mgr_delegations:
        raise ValueError(
                'Expected delegation to "pkg_mgr.json" in key manager metadata.')
    car.common.checkformat_delegation(
            key_mgr_delegations['pkg_mgr.json'])


    # Doing delegation processing.
    car.authentication.verify_delegation('pkg_mgr.json', signable, key_mgr)

    print(
            '\n\nSuccess: signature over package metadata verified based on '
            'trusted key manager metadata.')


if __name__ == '__main__':
  main()
