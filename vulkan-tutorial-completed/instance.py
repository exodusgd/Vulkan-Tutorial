from vulkan import *

import glfw

def check_extension_support(extensionsToCheck):

    supportedExtensions = []
    for extension in vkEnumerateInstanceExtensionProperties(None):
        supportedExtensions.append(extension.extensionName)

    print("------------- Supported Extensions -------------")
    for extension in supportedExtensions:
        print(f"{extension}")

    for extension in extensionsToCheck:
        if extension not in supportedExtensions:
            return False

    return True

def create_instance(applicationName):

    vulkanVersion = VK_MAKE_VERSION(1, 0, 0)

    appInfo = VkApplicationInfo(
            pApplicationName = applicationName,
            apiVersion = vulkanVersion
    )

    requiredExtensions = glfw.get_required_instance_extensions()
    print("------------- Required Extensions -------------")
    for extension in requiredExtensions:
        print(f"{extension}")

    if check_extension_support(requiredExtensions):
        createInfo = VkInstanceCreateInfo(
            pApplicationInfo = appInfo,
            enabledExtensionCount = len(requiredExtensions),
            ppEnabledExtensionNames = requiredExtensions
            )
        
        return vkCreateInstance(createInfo, None)
