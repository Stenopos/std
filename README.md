# Stenopos Standard Library

The standard library for the [Stenopos programming language](https://stenopos.github.io).

## Modules

| Module | Description | Status |
|--------|-------------|--------|
| `io` | File and console I/O | In development |
| `collections` | Lists, maps, sets | In development |
| `math` | Math functions and constants | In development |
| `string` | String utilities | In development |
| `kernel` | Linux kernel-module FFI bindings (printk, uaccess, chrdev, errno) | Designed |

## Using the standard library

```stenopos
import io.file
import math
import collections.list

str content = io.file.read("data.txt")
float64 root = math.sqrt(2.0)
```

## Built-in string methods

These are available on any `str` value without an import:

```stenopos
str s = "Hello, World!"
int32 n = s.len()
bool b = s.contains("World")
str u = s.to_upper()
str l = s.to_lower()
str t = s.trim()
str r = s.replace("World", "Stenopos")
```

## Writing a Linux kernel module

The `kernel` module wraps the C kernel ABI (it does not reimplement the
kernel). Import the pieces you need instead of re-declaring externs:

```stenopos
import kernel.printk.{pr_info}
import kernel.uaccess.{copy_to_user_ok}
import kernel.chrdev.{FileOperations, register_chrdev}
import kernel.errno.{EFAULT}
import kernel.module.MODULE_OK

@section(".init.text")
pub func hello_init() -> int32 {
    pr_info("hello from a Stenopos module")
    return MODULE_OK
}

@section(".exit.text")
pub func hello_exit() -> void {
    pr_info("goodbye")
}
```

See `examples/showcase/kernel_module.sten` for a complete character device.
Building a real `.ko` needs freestanding kernel-ABI codegen + Kbuild (roadmap
Phase 18); the bindings define the intended surface today.

## Contributing

Each module lives in its own directory with a `mod.sten` entry point. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Documentation

Full API reference: [stenopos.github.io/reference/stdlib](https://stenopos.github.io/reference/stdlib/)
