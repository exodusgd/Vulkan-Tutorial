
# statically load vulkan library
from vulkan import *

import glfw
import glfw.GLFW as GLFW_CONSTANTS

# TODO: import instance file

import device
import swapchain
import pipeline
import framebuffer
import commands

class Sync:

    def make_semaphore(device):

        semaphoreInfo = VkSemaphoreCreateInfo()

        try:
            return vkCreateSemaphore(device, semaphoreInfo, None)
    
        except:
            return None

    def make_fence(device):

        fenceInfo = VkFenceCreateInfo(
            flags = VK_FENCE_CREATE_SIGNALED_BIT
        )

        try:
            return vkCreateFence(device, fenceInfo, None)
    
        except:
            return None

class Engine:

    def __init__(self, width, height, window, appName):

        # glfw window parameters
        self.width = width
        self.height = height

        self.window = window
        self.appName = appName
        
        self.make_instance()
        self.make_device()
        self.make_pipeline()
        self.finalize_setup()
    
    def make_instance(self):
        # TODO: create the vulkan instance
        self.instance = None

        vulkanSurface = ffi.new("VkSurfaceKHR*")
        if (glfw.create_window_surface(
            instance = self.instance,
            window = self.window,
            allocator = None,
            surface = vulkanSurface
            ) == VK_SUCCESS
        ):
            self.surface = vulkanSurface[0]
    
    def make_device(self):

        self.physicalDevice = device.choose_physical_device(self.instance)
        self.device = device.create_logical_device(
            physicalDevice = self.physicalDevice, instance = self.instance, 
            surface = self.surface
        )
        queues = device.get_queues(
            physicalDevice = self.physicalDevice, logicalDevice = self.device, 
            instance = self.instance, surface = self.surface
        )
        self.graphicsQueue = queues[0]
        self.presentQueue = queues[1]
        
        bundle = swapchain.create_swapchain(
            self.instance, self.device, self.physicalDevice, self.surface,
            self.width, self.height
        )

        self.swapchain = bundle.swapchain
        self.swapchainFrames = bundle.frames
        self.swapchainFormat = bundle.format
        self.swapchainExtent = bundle.extent

    def make_pipeline(self):

        inputBundle = pipeline.InputBundle(
            device = self.device,
            swapchainImageFormat = self.swapchainFormat,
            swapchainExtent = self.swapchainExtent,

            # paths to the shader spir-v files
            vertexFilepath = "shaders/vert.spv",
            fragmentFilepath = "shaders/frag.spv"
        )

        outputBundle = pipeline.create_graphics_pipeline(inputBundle)

        self.pipelineLayout = outputBundle.pipelineLayout
        self.renderpass = outputBundle.renderPass
        self.pipeline = outputBundle.pipeline
    
    def finalize_setup(self):

        framebufferInput = framebuffer.framebufferInput()
        framebufferInput.device = self.device
        framebufferInput.renderpass = self.renderpass
        framebufferInput.swapchainExtent = self.swapchainExtent
        framebuffer.make_framebuffers(
            framebufferInput, self.swapchainFrames
        )

        commandPoolInput = commands.commandPoolInputChunk()
        commandPoolInput.device = self.device
        commandPoolInput.physicalDevice = self.physicalDevice
        commandPoolInput.surface = self.surface
        commandPoolInput.instance = self.instance
        self.commandPool = commands.make_command_pool(
            commandPoolInput
        )

        commandbufferInput = commands.commandbufferInputChunk()
        commandbufferInput.device = self.device
        commandbufferInput.commandPool = self.commandPool
        commandbufferInput.frames = self.swapchainFrames
        self.mainCommandbuffer = commands.make_command_buffers(
            commandbufferInput
        )

        self.inFlightFence = Sync.make_fence(self.device)
        self.imageAvailable = Sync.make_semaphore(self.device)
        self.renderFinished = Sync.make_semaphore(self.device)

    def record_draw_commands(self, commandBuffer, imageIndex):

        beginInfo = VkCommandBufferBeginInfo()

        try:
            vkBeginCommandBuffer(commandBuffer, beginInfo)
        except:
            print("Failed to begin recording command buffer")
        
        renderpassInfo = VkRenderPassBeginInfo(
            renderPass = self.renderpass,
            framebuffer = self.swapchainFrames[imageIndex].framebuffer,
            renderArea = [[0,0], self.swapchainExtent]
        )
        
        # color used for the background
        clearColor = VkClearValue([[0.67, 0.08, 0.16, 1.0]])
        renderpassInfo.clearValueCount = 1
        renderpassInfo.pClearValues = ffi.addressof(clearColor)
        
        vkCmdBeginRenderPass(commandBuffer, renderpassInfo, VK_SUBPASS_CONTENTS_INLINE)
        
        vkCmdBindPipeline(commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)
        
        vkCmdDraw(
            commandBuffer = commandBuffer, vertexCount = 3, 
            instanceCount = 1, firstVertex = 0, firstInstance = 0
        )
        
        vkCmdEndRenderPass(commandBuffer)
        
        try:
            vkEndCommandBuffer(commandBuffer)
        except:
            print("Failed to end recording command buffer")
    
    def render(self):

        # grab instance procedures
        vkAcquireNextImageKHR = vkGetDeviceProcAddr(self.device, 'vkAcquireNextImageKHR')
        vkQueuePresentKHR = vkGetDeviceProcAddr(self.device, 'vkQueuePresentKHR')

        vkWaitForFences(
            device = self.device, fenceCount = 1, pFences = [self.inFlightFence,], 
            waitAll = VK_TRUE, timeout = 1000000000
        )
        vkResetFences(
            device = self.device, fenceCount = 1, pFences = [self.inFlightFence,]
        )

        imageIndex = vkAcquireNextImageKHR(
            device = self.device, swapchain = self.swapchain, timeout = 1000000000, 
            semaphore = self.imageAvailable, fence = VK_NULL_HANDLE
        )

        commandBuffer = self.swapchainFrames[imageIndex].commandbuffer
        vkResetCommandBuffer(commandBuffer = commandBuffer, flags = 0)
        self.record_draw_commands(commandBuffer, imageIndex)

        submitInfo = VkSubmitInfo(
            waitSemaphoreCount = 1, pWaitSemaphores = [self.imageAvailable,], 
            pWaitDstStageMask=[VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,],
            commandBufferCount = 1, pCommandBuffers = [commandBuffer,], signalSemaphoreCount = 1,
            pSignalSemaphores = [self.renderFinished,]
        )

        try:
            vkQueueSubmit(
                queue = self.graphicsQueue, submitCount = 1, 
                pSubmits = submitInfo, fence = self.inFlightFence
            )
        except:
            print("Failed to submit draw commands")
        
        presentInfo = VkPresentInfoKHR(
            waitSemaphoreCount = 1, pWaitSemaphores = [self.renderFinished,],
            swapchainCount = 1, pSwapchains = [self.swapchain,],
            pImageIndices = [imageIndex,]
        )
        vkQueuePresentKHR(self.presentQueue, presentInfo)

    def close(self):

        vkDeviceWaitIdle(self.device)

        vkDestroyFence(self.device, self.inFlightFence, None)
        vkDestroySemaphore(self.device, self.imageAvailable, None)
        vkDestroySemaphore(self.device, self.renderFinished, None)

        vkDestroyCommandPool(self.device, self.commandPool, None)

        vkDestroyPipeline(self.device, self.pipeline, None)
        vkDestroyPipelineLayout(self.device, self.pipelineLayout, None)
        vkDestroyRenderPass(self.device, self.renderpass, None)
        
        for frame in self.swapchainFrames:
            vkDestroyImageView(
                device = self.device, imageView = frame.image_view, pAllocator = None
            )
            vkDestroyFramebuffer(
                device = self.device, framebuffer = frame.framebuffer, pAllocator = None
            )
        
        destructionFunction = vkGetDeviceProcAddr(self.device, 'vkDestroySwapchainKHR')
        destructionFunction(self.device, self.swapchain, None)
        vkDestroyDevice(
            device = self.device, pAllocator = None
        )
        
        destructionFunction = vkGetInstanceProcAddr(self.instance, "vkDestroySurfaceKHR")
        destructionFunction(self.instance, self.surface, None)

        vkDestroyInstance(self.instance, None)

        glfw.terminate()


class App():

    def __init__(self, width, height, appName):
        self.appName = appName
        self.create_glfw_window(width, height)

        self.graphicsEngine = Engine(width, height, self.window, appName)
        

    def create_glfw_window(self, width, height):
        glfw.init()

        glfw.window_hint(GLFW_CONSTANTS.GLFW_CLIENT_API, GLFW_CONSTANTS.GLFW_NO_API)
        glfw.window_hint(GLFW_CONSTANTS.GLFW_RESIZABLE, GLFW_CONSTANTS.GLFW_FALSE)

        self.window = glfw.create_window(width, height, self.appName, None, None)

    def run(self):
        while not glfw.window_should_close(self.window):

            glfw.poll_events()
            self.graphicsEngine.render()

    def close(self):
        self.graphicsEngine.close()


if __name__ == "__main__":
    vulkanApp = App(640, 480, "Vulkan Tutorial")
    
    vulkanApp.run()

    vulkanApp.close()