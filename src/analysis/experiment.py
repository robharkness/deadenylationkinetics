class FretExperiment():

    def __init__(self, data, hybridization_params):

        self.data = data
        self.data_groups = data.groupby('Enzyme')
        self.time = []
        self.fret = []
        self.unique_time = []
        self.mean_fret = []
        self.mean_norm_fret = []
        self.fret_std = []
        self.norm_fret_std = []
        self.mean_resid=[]
        self.resid_std=[]
        self.enzyme = data.Enzyme.unique()
        self.rna = data.RNA.unique().astype(float) # Need to either make float or index from unique() with [0] because otherwise makes a ragged nested array in kinetics C0 later
        self.QT = hybridization_params['QT']
        self.n = hybridization_params['n']
        self.dGo = hybridization_params['dGo']
        self.alpha = hybridization_params['alpha']
        self.temperature = hybridization_params['Temperature']

        for ind, group in self.data_groups: # Convert data frame into list-of-lists of time, fret, and errors
            self.time.append(group.Time.values)
            self.fret.append(group.FRET.values)