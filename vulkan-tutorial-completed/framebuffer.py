# statically load vulkan library
from vulkan import *

class SwapChainFrame:

    def __init__(self):
        
        self.image = None
        self.image_view = None
        self.framebuffer = None
        self.commandbuffer = None

class framebufferInput:

    def __init__(self):

        self.device = None
        self.renderpass = None
        self.swapchainExtent = None

def make_framebuffers(inputChunk, frames):

    for i,frame in enumerate(frames):

        attachments = [frame.image_view,]

        framebufferInfo = VkFramebufferCreateInfo(
            renderPass = inputChunk.renderpass,
            attachmentCount = 1,
            pAttachments = attachments,
            width = inputChunk.swapchainExtent.width,
            height = inputChunk.swapchainExtent.height,
            layers=1
        )

        try:
            frame.framebuffer = vkCreateFramebuffer(
                inputChunk.device, framebufferInfo, None
            )
            
        except:
            print(f"Failed to make framebuffer for frame {i}")
