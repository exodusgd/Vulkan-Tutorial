# statically load vulkan library
from vulkan import *

import queue_families


def check_device_extension_support(device, requestedExtensions):

    supportedExtensions = [
        extension.extensionName 
        for extension in vkEnumerateDeviceExtensionProperties(device, None)
    ]

    for extension in requestedExtensions:
        if extension not in supportedExtensions:
            return False
    
    return True

def is_suitable(device):

    requestedExtensions = [
        VK_KHR_SWAPCHAIN_EXTENSION_NAME
    ]

    if check_device_extension_support(device, requestedExtensions):
        return True

    return False

def choose_physical_device(instance):

    availableDevices = vkEnumeratePhysicalDevices(instance)

    # check if a suitable device can be found
    for device in availableDevices:
        if is_suitable(device):
            return device

    return None

def create_logical_device(physicalDevice, instance, surface):

    indices = queue_families.find_queue_families(physicalDevice, instance, surface)
    uniqueIndices = [indices.graphicsFamily,]
    if indices.graphicsFamily != indices.presentFamily:
        uniqueIndices.append(indices.presentFamily)
    
    queueCreateInfo = []
    for queueFamilyIndex in uniqueIndices:
        queueCreateInfo.append(
            VkDeviceQueueCreateInfo(
                queueFamilyIndex = queueFamilyIndex,
                queueCount = 1,
                pQueuePriorities = [1.0,]
            )
        )

    deviceFeatures = VkPhysicalDeviceFeatures()

    enabledLayers = []
    
    deviceExtensions = [
        VK_KHR_SWAPCHAIN_EXTENSION_NAME,
    ]

    createInfo = VkDeviceCreateInfo(
        queueCreateInfoCount = len(queueCreateInfo),
        pQueueCreateInfos = queueCreateInfo,
        enabledExtensionCount = len(deviceExtensions),
        ppEnabledExtensionNames = deviceExtensions,
        pEnabledFeatures = [deviceFeatures,],
        enabledLayerCount = len(enabledLayers),
        ppEnabledLayerNames = enabledLayers
    )

    return vkCreateDevice(
        physicalDevice = physicalDevice, pCreateInfo = [createInfo,], pAllocator = None
    )

def get_queues(physicalDevice, logicalDevice, instance, surface):

    indices = queue_families.find_queue_families(physicalDevice, instance, surface)
    return [
        vkGetDeviceQueue(
            device = logicalDevice,
            queueFamilyIndex = indices.graphicsFamily,
            queueIndex = 0
        ),
        vkGetDeviceQueue(
            device = logicalDevice,
            queueFamilyIndex = indices.presentFamily,
            queueIndex = 0
        ),
    ]
