from __future__ import print_function
import numpy as np
import random
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
from tornasole.pytorch.hook import *
from tornasole.pytorch.torch_collection import *


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.add_module('conv1', nn.Conv2d(1, 20, 5, 1))
        self.add_module('relu0', nn.ReLU())
        self.add_module('max_pool', nn.MaxPool2d(2, stride=2))
        self.add_module('conv2', nn.Conv2d(20, 50, 5, 1))
        self.add_module('relu1', nn.ReLU())
        self.add_module('max_pool2', nn.MaxPool2d(2, stride=2))
        self.add_module('fc1', nn.Linear(4*4*50, 500))
        self.add_module('relu2', nn.ReLU())
        self.add_module('fc2', nn.Linear(500, 10))


    def forward(self, x):
        x = self.relu0(self.conv1(x))
        x = self.max_pool(x)
        x = self.relu1(self.conv2(x))
        x = self.max_pool2(x)
        x = x.view(-1, 4*4*50)
        x = self.relu2(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

# Create a tornasole hook. The initilization of hook determines which tensors
# are logged while training is in progress.
# Following function shows the default initilization that enables logging of
# weights, biases and gradients in the model.
def create_tornasole_hook(output_dir, module=None, hook_type='saveall', save_steps=None):
    # Create a hook that logs weights, biases, gradients and inputs/ouputs of model
    if hook_type == 'saveall':
        hook = TornasoleHook(out_dir=output_dir, save_config=SaveConfig(save_steps=save_steps), save_all=True)
    elif hook_type == 'module-input-output':
        # The names of input and output tensors of a module are in following format
        # Inputs :  <module_name>_input_<input_index>, and
        # Output :  <module_name>_output
        # In order to log the inputs and output of a module, we will create a collection as follows:
        assert module is not None
        get_collection('l_mod').add_module_tensors(module, inputs=True, outputs=True)

        # Create a hook that logs weights, biases, gradients and inputs/outputs of model
        hook = TornasoleHook(out_dir=output_dir, save_config=SaveConfig(save_steps=save_steps), 
                                include_collections=['weights', 'gradients', 'bias','l_mod'])
    elif hook_type == 'weights-bias-gradients':
        save_config = SaveConfig(save_steps=save_steps)
        # Create a hook that logs ONLY weights, biases, and gradients
        hook = TornasoleHook(out_dir=output_dir, save_config=save_config)
    return hook

def train(model, device, optimizer, num_steps=500, save_steps=[]):
    model.train()
    count = 0
    # for batch_idx, (data, target) in enumerate(train_loader):
    for i in range(num_steps):
        batch_size=32
        data, target = torch.rand(batch_size, 1, 28, 28), torch.rand(batch_size).long()
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(Variable(data, requires_grad = True))
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()

parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                    help='input batch size for training (default: 64)')
parser.add_argument('--epochs', type=int, default=1, metavar='N',
                    help='number of epochs to train (default: 1)')
parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                    help='learning rate (default: 0.01)')
parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                    help='SGD momentum (default: 0.9)')
parser.add_argument('--tornasole-frequency', type=int, default=10, help='frequency with which to save steps')
parser.add_argument('--steps', type=int, default=100, help='number of steps')
parser.add_argument('--tornasole_path', type=str, help="output directory to save data in", default='./tornasole-testing/demo/')
parser.add_argument('--hook-type', type=str, choices=['saveall', 'module-input-output', 'weights-bias-gradients'], default='saveall')
parser.add_argument('--random-seed', type=bool, default=False)

args = parser.parse_args()

if args.random_seed:
    torch.manual_seed(2)
    np.random.seed(2)
    random.seed(12)

hook_type = 'saveall'
device = torch.device("cpu")
save_steps = [(i+1) * args.tornasole_frequency for i in range(args.steps//args.tornasole_frequency)]
model = Net().to(device)
hook = create_tornasole_hook(args.tornasole_path, model, hook_type, save_steps=save_steps)

hook.register_hook(model)
optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)
train(model, device, optimizer, num_steps=args.steps, save_steps=save_steps)