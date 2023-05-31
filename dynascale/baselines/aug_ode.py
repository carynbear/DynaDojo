class AugODE(Model):
    def __init__(self, embed_dim: int, timesteps: int, max_control_cost: float, lr=3e-2, aug_dim = 2, **kwargs):
        super().__init__()

        self.model = nn.Sequential(nn.Linear(embed_dim + aug_dim, 32), nn.Softplus(), nn.Linear(32, embed_dim))
        self.lr = lr
        self.aug_dim = aug_dim
        self.timesteps = timesteps
        self.mse_loss = nn.MSELoss()
        self.opt = torch.optim.Adam(self.model.parameters(), self.lr)

    def forward(self, t, state):
        zeros = torch.zeros(self.aug_dim)
        #aug_state = torch.cat((state, zeros))
        aug_state = torch.nn.functional.pad(input=state, pad=(0, self.aug_dim), mode='constant', value=0)
        
        dx = self.model(aug_state)
        return dx

    def fit(self, x: np.ndarray, epochs=100, **kwargs):
        x = torch.tensor(x, dtype=torch.float32)
        state = x[:, 0, :]
        step = end = epochs/self.timesteps
        
        for _ in range(epochs):
            if _ % step == 0:
                t = torch.linspace(0.0, end, self.timesteps)
                end += step
            self.opt.zero_grad()
            pred = odeint(self.forward, state, t, method='midpoint')
            pred = pred.transpose(0, 1)
            loss = self.mse_loss(pred, x).float()
            loss.backward()
            self.opt.step()

    def predict(self, x0):
        x0 = torch.tensor(x0, dtype=torch.float32)
        t = torch.linspace(0.0, self.timesteps, self.timesteps)
        return odeint(self, x0, t)
