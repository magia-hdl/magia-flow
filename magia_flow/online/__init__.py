"""
Integrating Magia to other online services.

Code under this package is responsible for integrating Magia to other online services.

WARNING:
Elaborated SystemVerilog code will be sent to 3rd-party services.
The service party will have access to the code and may store it for their own purposes.
Don't use this package if you are developing a proprietary IP or any closed-source project.
"""

from .digitaljs import elaborate_on_digitaljs

__all__ = [
    "elaborate_on_digitaljs"
]
