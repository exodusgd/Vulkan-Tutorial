# statically load vulkan library
from vulkan import *

import framebuffer
import queue_families

class SwapChainSupportDetails:


    def __init__(self):
        
        self.capabilities = None
        self.formats = None
        self.presentModes = None

class SwapChainBundle:


    def __init__(self):
        
        self.swapchain = None
        self.frames = []
        self.format = None
        self.extent = None

def query_swapchain_support(instance, physicalDevice, surface):

    support = SwapChainSupportDetails()
    vkGetPhysicalDeviceSurfaceCapabilitiesKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceCapabilitiesKHR')
    support.capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice, surface)

    vkGetPhysicalDeviceSurfaceFormatsKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceFormatsKHR')
    support.formats = vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface)

    vkGetPhysicalDeviceSurfacePresentModesKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfacePresentModesKHR')
    support.presentModes = vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice, surface)

    return support

def choose_swapchain_surface_format(formats):

    for format in formats:
        if (format.format == VK_FORMAT_B8G8R8A8_UNORM
            and format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
            return format

    return formats[0]

def choose_swapchain_present_mode(presentModes):
        
    for presentMode in presentModes:
        if presentMode == VK_PRESENT_MODE_MAILBOX_KHR:
            return presentMode

    return VK_PRESENT_MODE_FIFO_KHR

def choose_swapchain_extent(width, height, capabilities):
    
    extent = VkExtent2D(width, height)

    extent.width = min(
        capabilities.maxImageExtent.width, 
        max(capabilities.minImageExtent.width, extent.width)
    )

    extent.height = min(
        capabilities.maxImageExtent.height,
        max(capabilities.minImageExtent.height, extent.height)
    )

    return extent

def create_swapchain(instance, logicalDevice, physicalDevice, surface, width, height):

    support = query_swapchain_support(instance, physicalDevice, surface)

    format = choose_swapchain_surface_format(support.formats)

    presentMode = choose_swapchain_present_mode(support.presentModes)

    extent = choose_swapchain_extent(width, height, support.capabilities)

    imageCount = min(
        support.capabilities.maxImageCount,
        support.capabilities.minImageCount + 1
    )

    indices = queue_families.find_queue_families(physicalDevice, instance, surface)
    queueFamilyIndices = [
        indices.graphicsFamily, indices.presentFamily
    ]
    if (indices.graphicsFamily != indices.presentFamily):
        imageSharingMode = VK_SHARING_MODE_CONCURRENT
        queueFamilyIndexCount = 2
        pQueueFamilyIndices = queueFamilyIndices
    else:
        imageSharingMode = VK_SHARING_MODE_EXCLUSIVE
        queueFamilyIndexCount = 0
        pQueueFamilyIndices = None

    createInfo = VkSwapchainCreateInfoKHR(
        surface = surface, minImageCount = imageCount, imageFormat = format.format,
        imageColorSpace = format.colorSpace, imageExtent = extent, imageArrayLayers = 1,
        imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT, imageSharingMode = imageSharingMode,
        queueFamilyIndexCount = queueFamilyIndexCount, pQueueFamilyIndices = pQueueFamilyIndices,
        preTransform = support.capabilities.currentTransform, compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
        presentMode = presentMode, clipped = VK_TRUE
    )

    bundle = SwapChainBundle()

    vkCreateSwapchainKHR = vkGetDeviceProcAddr(logicalDevice, 'vkCreateSwapchainKHR')
    bundle.swapchain = vkCreateSwapchainKHR(logicalDevice, createInfo, None)
    vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(logicalDevice, 'vkGetSwapchainImagesKHR')

    images = vkGetSwapchainImagesKHR(logicalDevice, bundle.swapchain)

    for image in images:

        components = VkComponentMapping(
            r = VK_COMPONENT_SWIZZLE_IDENTITY,
            g = VK_COMPONENT_SWIZZLE_IDENTITY,
            b = VK_COMPONENT_SWIZZLE_IDENTITY,
            a = VK_COMPONENT_SWIZZLE_IDENTITY
        )

        subresourceRange = VkImageSubresourceRange(
            aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
            baseMipLevel = 0, levelCount = 1,
            baseArrayLayer = 0, layerCount = 1
        )

        create_info = VkImageViewCreateInfo(
            image = image, viewType = VK_IMAGE_VIEW_TYPE_2D,
            format = format.format, components = components,
            subresourceRange = subresourceRange
        )

        swapchain_frame = framebuffer.SwapChainFrame()
        swapchain_frame.image = image
        swapchain_frame.image_view = vkCreateImageView(
            device = logicalDevice, pCreateInfo = create_info, pAllocator = None
        )
        bundle.frames.append(swapchain_frame)
    
    bundle.format = format.format
    bundle.extent = extent

    return bundle