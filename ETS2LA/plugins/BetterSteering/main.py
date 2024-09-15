import ctypes
import os
import math

# 加载 DLL 文件
dll_path = os.path.abspath("memoryscan.dll")
scanner = ctypes.CDLL(dll_path)

# 定义函数参数和返回类型
scanner.scanMemory.argtypes = [ctypes.c_wchar_p, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_int)]
scanner.scanMemory.restype = ctypes.POINTER(ctypes.c_ulonglong)


def find_float_values_addresses(process_name, value_to_find, epsilon=0.000001):
    process_name_wchar = ctypes.c_wchar_p(process_name)
    length = ctypes.c_int(0)
    addresses_ptr = scanner.scanMemory(process_name_wchar, ctypes.c_float(value_to_find), ctypes.c_float(epsilon),
                                       ctypes.byref(length))

    addresses = []
    for i in range(length.value):
        addresses.append(addresses_ptr[i])
    return addresses


def main():
    process_name = input("请输入目标进程的名称（例如 example.exe）: ")
    while True:
        value_to_find = float(input("请输入要查找的单精度浮点数值: "))

        # 初次搜索
        addresses = find_float_values_addresses(process_name, value_to_find)

        if 0 < len(addresses) <= 3:
            print(f"找到 {len(addresses)} 个匹配的地址: {[hex(addr) for addr in addresses]}")
            for addr in addresses:
                print(f"地址 {hex(addr)}: 进程 {process_name} 中的值 {value_to_find}")
            break
        elif len(addresses) > 3:
            print(f"找到超过三个匹配的地址，共有 {len(addresses)} 个，进行第二次搜索...")

            while len(addresses) > 3:
                restricted_addresses = set(addresses)  # 使用集合提高查找效率
                value_to_find = float(input("请输入要查找的单精度浮点数值，用于精确搜索: "))

                # 只在初次搜索找到的地址范围内再次搜索
                new_addresses = find_float_values_addresses(process_name, value_to_find)

                # 过滤出在限制范围内的新地址
                addresses = [addr for addr in new_addresses if addr in restricted_addresses]

                print(f"二次搜索找到 {len(addresses)} 个匹配的地址。")

                if 0 < len(addresses) <= 3:
                    print(f"最终找到 {len(addresses)} 个匹配的地址: {[hex(addr) for addr in addresses]}")
                    for addr in addresses:
                        print(f"地址 {hex(addr)}: 进程 {process_name} 中的值 {value_to_find}")
                    break
        else:
            print(f"找到少于三个匹配的地址，共有 {len(addresses)} 个，重新输入数值进行扫描...")


if __name__ == "__main__":
    main()
