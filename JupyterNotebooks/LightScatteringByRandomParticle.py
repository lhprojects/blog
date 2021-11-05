
import matplotlib.pyplot as plt

def show_dia():
    np.random.seed(0)
    x = np.random.rand(5) - 0.5
    y = np.random.rand(5) - 0.5

    fig = plt.figure(figsize=(4,4))
    plt.scatter(x, y)
    plt.axis('off')
    plt.xlim((-0.2,0.75))
    plt.ylim((-0.2,0.75))
    for ax,ay in zip(x,y):
        plt.plot([-2,ax], [ay, ay], color="red")
        plt.plot([ax, 2], [ay, ay + (2-ax)], color="red")
    plt.text(0.75,0.25,r"$(k''_x,k''_y,k''_z)$")
    plt.text(-0.5,0.25,r"$(k'_x,k'_y,k'_z)$")
    #%mkdir  LightScatterringByRandomParticle
    #plt.savefig("LightScatterringByRandomParticle/lightscatterdia.png")
    plt.show()
    

    
    
    

import numpy as np
import numba
import matplotlib.pyplot as plt

# light come form -z 
# scatter to y
@numba.njit
def cal_phi(z, y, sintheta, costheta, k):
    phi = (z * (1 - costheta) - y*sintheta)*k
    return phi

@numba.njit
def MC_A(thetas, N, lamb, width_z, width_y, model):
    k = 2*np.pi/lamb
    
    coss = np.full_like(thetas, 0.)
    sins = np.full_like(thetas, 0.)
    
    sinthetas = np.sin(thetas)
    costhetas = np.cos(thetas)
    
    model_GAUSS = 0
    model_BOX = 1
    model_ = 0
    if model == "gauss":
        model_ = model_GAUSS
    elif model == "box":
        model_ = model_BOX
        
    for i in range(N):
        if model_ == model_GAUSS:
            z = np.random.normal()*width_z
            y = np.random.normal()*width_y
        elif model_ == model_BOX:
            z = (np.random.rand()-0.5)*width_z
            y = (np.random.rand()-0.5)*width_y
        
        for t, theta in enumerate(thetas): 
            phi = cal_phi(z, y, sinthetas[t], costhetas[t], k)
            #phi = 2*np.pi*np.random.rand()
            #print(z, y, phi)
            coss[t] += np.cos(phi)
            sins[t] += np.sin(phi)
            
    as_ = coss**2 + sins**2
            
    return as_/N

def cal_A(thetas, N, lamb, width_z, width_y, model):
    k = 2*np.pi/lamb
    
    As = np.full_like(thetas, 0.)
    
    ky = -np.sin(thetas)*k
    kz = (1-np.cos(thetas))*k
    if model == "gauss":
        def G_ratio(omega, width):
            alpha = 1/(2*width*width)
            return np.exp(-omega**2/(4*alpha))
    elif model == "box":
        def G_ratio(omega, width):
            a = 1/width
            x = omega/(2*np.pi*a)
            return np.sinc(x)
        
    return 1 + N*G_ratio(ky, width_y)*G_ratio(-ky, width_y)*G_ratio(kz, width_z)*G_ratio(-kz, width_z)
        
        
            

def plot(N, lamb, model="", 
         repeat=1, simulate=True,
         width_z=None, width_y=None, width=None,
         plot_range=1., plot_points=32, ax=None,
         plot_upper=False,
         title=None):
    
    N = int(N)
    thetas = np.linspace(-np.pi*plot_range, np.pi*plot_range,plot_points)    
    if width_z is None:
        width_z = width
    if width_y is None:
        width_y = width
    if width_z is None or width_y is None:
        assert False
        
    # simulate
    if simulate:
        Ass = np.empty(shape=(repeat, thetas.shape[0]))
        for r in range(repeat):
            Ass[r] = MC_A(thetas, N, lamb, width_z=width_z, width_y=width_y, model=model)
        As = Ass.mean(axis=0)
    
    Bs = cal_A(thetas, N, lamb, width_z=width_z, width_y=width_y, model=model)
    
    
    # begin plot
    show=False
    if ax is None:
        plt.figure(figsize=(4,4))
        ax = plt.gca()
        
    if simulate:
        for r in range(repeat):
            #ax.plot(thetas, Ass[r,:], label="numerical")
            pass
        ax.plot(thetas, As, label="numerical")
            
        if repeat >= 2 and plot_upper:
            VarAs = Ass.std(axis=0)
            ax.plot(thetas, As + VarAs, label="numerical + 1$\sigma$", linestyle="--")
            
        
        
    ax.set_xlabel(r"$\theta$")
    ax.plot(thetas, Bs, label="theory")
    ax.set_yscale("log")
    ax.set_title(title)
    ax.legend()
    
    if show:
        plt.show()
