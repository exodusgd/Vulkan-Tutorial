# statically load vulkan library
from vulkan import *

class QueueFamilyIndices:

    def __init__(self):

        self.graphicsFamily = None
        self.presentFamily = None
    
    def is_complete(self):

        return not(self.graphicsFamily is None or self.presentFamily is None)
    
def find_queue_families(device, instance, surface):
        
    indices = QueueFamilyIndices()

    surfaceSupport = vkGetInstanceProcAddr(instance, "vkGetPhysicalDeviceSurfaceSupportKHR")

    queueFamilies = vkGetPhysicalDeviceQueueFamilyProperties(device)

    for i,queueFamily in enumerate(queueFamilies):

        if queueFamily.queueFlags & VK_QUEUE_GRAPHICS_BIT:
            indices.graphicsFamily = i
        
        if surfaceSupport(device, i, surface):
            indices.presentFamily = i

        if indices.is_complete():
            break

    return indices