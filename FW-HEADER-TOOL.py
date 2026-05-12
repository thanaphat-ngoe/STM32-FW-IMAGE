import sys
import struct
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

# --- Configuration ---
HEADER_SIZE      = 256    # Exact size of FirmwareHeader_TypeDef

# ---------------------------------------------------------
# NEW OFFSETS (Based on the updated C Struct)
# ---------------------------------------------------------
OFFSET_VERSION   = 0x08  # 8
OFFSET_SIZE      = 0x0C  # 12
OFFSET_SIG_R     = 0x10  # 16
OFFSET_SIG_S     = 0x30  # 48
OFFSET_CRC32     = 0xFC  # 252

def crc32_ethernet(data: bytes) -> int:
    crc = 0xFFFFFFFF
    padded_data = data + b'\x00' * ((4 - len(data) % 4) % 4)
    for i in range(0, len(padded_data), 4):
        word = struct.unpack_from(">I", padded_data, i)[0] 
        crc ^= word
        for _ in range(32):
            if crc & 0x80000000:
                crc = (crc << 1) ^ 0x04C11DB7
            else:
                crc = (crc << 1)
            crc &= 0xFFFFFFFF
    return crc

def fill_firmware_header(app_in_path, app_out_path, version_num, priv_key_path):
    try:
        # PROCESS FIRMWARE & HEADER
        with open(app_in_path, "rb") as f:
            app_data = bytearray(f.read())

        payload = app_data[HEADER_SIZE:]
        fw_size = len(payload)

        print(f"Injecting Metadata:")
        print(f" - Version:      {version_num}")
        print(f" - Payload Size: {fw_size} bytes")

        struct.pack_into("<I", app_data, OFFSET_VERSION, version_num)
        struct.pack_into("<I", app_data, OFFSET_SIZE, fw_size)

        # SIGNATURE GENERATION (ECDSA secp256r1)
        print("\nCryptography & Integrity:")
        print(" - Generating ECDSA SHA-256 Signature...")
        
        with open(priv_key_path, "rb") as key_file:
            priv_key = serialization.load_pem_private_key(key_file.read(), password=None)
        
        der_signature = priv_key.sign(payload, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der_signature)

        print(f"   > Signature R: 0x{r:064X}")
        print(f"   > Signature S: 0x{s:064X}")

        r_bytes = r.to_bytes(32, byteorder='big')
        s_bytes = s.to_bytes(32, byteorder='big')

        app_data[OFFSET_SIG_R : OFFSET_SIG_R + 32] = r_bytes
        app_data[OFFSET_SIG_S : OFFSET_SIG_S + 32] = s_bytes

        # CRC-32 CALCULATION
        print(" - Computing Hardware CRC-32...")
        data_for_crc = app_data[0:OFFSET_CRC32] + app_data[OFFSET_CRC32 + 4:]
        
        computed_crc = crc32_ethernet(data_for_crc)
        
        print(f"   > CRC-32:      0x{computed_crc:08X}")

        struct.pack_into("<I", app_data, OFFSET_CRC32, computed_crc)

        # WRITE FILLED APPLICATION OUTPUT
        with open(app_out_path, "wb") as f:
            f.write(app_data)

        print("\n" + "="*50)
        print(f"SUCCESS! Firmware header filled: '{app_out_path}'")
        print("="*50)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 5:
        version_arg = int(sys.argv[3])
        priv_key_arg = sys.argv[4]
        fill_firmware_header(sys.argv[1], sys.argv[2], version_arg, priv_key_arg)
    else:
        print("Usage: python FW-HEADER-TOOL.py <app_in.bin> <app_out.bin> <version_number> <private_key_path>")
        sys.exit(1)
