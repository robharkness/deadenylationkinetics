#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.backends.backend_pdf
import matplotlib.patheffects as path_effects
import matplotlib.colors as colors
import numpy as np
from scipy.interpolate import CubicSpline
from scipy import interpolate

class PlotHandler:

    def __init__(self, experiments, kinetic_models, hybridization_models, resids, normalized_resids, sample_name, best_fit_flag, residual_flag, bar_2d_flag, bar_3d_flag):

        self.experiments = experiments
        self.kinetic_models = kinetic_models
        self.hybridization_models = hybridization_models
        self.residuals = resids
        self.normalized_residuals = normalized_resids
        self.sample_name = sample_name
        self.timesample = [0,30,60,120,300,600,900,1200,1500,1800,2100,2400,3600] # Time points at which to make bar plots of the RNA populations

        self.best_fit_flag = best_fit_flag
        self.residual_flag = residual_flag
        self.bar_2d_flag = bar_2d_flag
        self.bar_3d_flag = bar_3d_flag

        unique_enzyme = self.experiments[0].enzyme # FRET plots
        slice = len(unique_enzyme) + 1
        points = (len(unique_enzyme) + 1)*(len(unique_enzyme) + 1)
        colormap = cm.inferno
        map_name = 'enzyme_colors'
        reversed = True
        self.get_colors(points, slice, colormap, map_name, reversed)
        self.enzyme_colors = self.enzyme_colors[1:]
        self.alphas = [1,0.9,0.8,0.7,0.6,0.5,0.4,0.3]

        t_pop_keys = [k for k in kinetic_models[0].concentrations.keys() if k not in ['E', 'E*']] # 2D and 3D bar plots
        slice = 18
        points = 324
        colormap = cm.coolwarm
        map_name = 't_pop_colors'
        reversed = False
        self.get_colors(points, slice, colormap, map_name, reversed)

        self.enzyme_bar_colors = ['#80cdc1', '#c7eae5'] # 2D bar plots

        self.pdf = make_pdf(f"{sample_name}_FRET_fits.pdf")
        plt.style.use('figure')

    def addattr(self, x, v):
        self.__dict__[x] = v

    @staticmethod
    def plot_best_fit(experiments, kinetic_models, hybridization_models, enz_colors, sample_name, pdf):

        for j, experiment in enumerate(experiments): # Plot individual replicates on separate plots to see fits more clearly
            kinetic_model = kinetic_models[j]
            hybridization_model = hybridization_models[j]

            data_fit_fig = plt.subplots(1,1,figsize=(7,5)) # Access fig with data_fit_fig[0], axis with data_fit_fig[1]
            normalized_data_fit_fig = plt.subplots(1,1,figsize=(7,5))

            max_time = round(np.max([np.max(v) for v in experiment.time]),-2)
            #xlim = [0-0.03*max_time, max_time+0.03*max_time]
            xlim = [0-0.01*max_time, 2800]
            #xticks = np.linspace(0,max_time,5)
            xticks = np.linspace(0,2800,5)

            for i, enzyme in enumerate(experiment.enzyme):
                color_idx = i
                rep_idx = j

                if rep_idx == 0:
                    line_label = f"{enzyme*1e6}"
                else:
                    line_label = '_Hidden'

                # FRET data plots
                data_fit_fig[1].plot(hybridization_model.time[i][1:],hybridization_model.fret[i][1:],color=enz_colors[color_idx],label=line_label)
                data_fit_fig[1].errorbar(experiment.time[i][1:],experiment.fret[i][1:],yerr=experiment.fret_error[i][1:],fmt='o',markersize=8,mfc='w',mec=enz_colors[color_idx],capsize=3,capthick=1.5,
                                         ecolor=enz_colors[color_idx])
                normalized_data_fit_fig[1].plot(hybridization_model.time[i][1:],hybridization_model.normalized_fret[i][1:],color=enz_colors[color_idx],label=line_label)
                normalized_data_fit_fig[1].errorbar(experiment.time[i][1:],hybridization_model.normalized_experimental_fret[i][1:],yerr=hybridization_model.normalized_fret_error[i][1:],fmt='o',markersize=8,
                                                    mfc='w',mec=enz_colors[color_idx],capsize=3,capthick=1.5,ecolor=enz_colors[color_idx])

            data_fit_fig[1].set_xlim(xlim)
            data_fit_fig[1].set_xticks(xticks)
            data_fit_fig[1].set_xlabel('Time (s)')
            data_fit_fig[1].set_ylabel('FRET')
            normalized_data_fit_fig[1].set_xlim(xlim)
            normalized_data_fit_fig[1].set_xticks(xticks)
            normalized_data_fit_fig[1].set_ylim([-0.25, 1.2])
            normalized_data_fit_fig[1].set_xlabel('Time (s)')
            normalized_data_fit_fig[1].set_ylabel('Normalized FRET')
            if len(experiments) > 1:
                data_fit_fig[1].set_title(f"Replicate {j+1}")
                normalized_data_fit_fig[1].set_title(f"Replicate {j+1}")
            else:
                data_fit_fig[1].set_title(f"Average of replicates")
                normalized_data_fit_fig[1].set_title(f"Average of replicates")
            L = normalized_data_fit_fig[1].legend(frameon=False,handlelength=0,handletextpad=0,loc='upper right',title=f"[{sample_name}] $\mu$M")
            for k,text in enumerate(L.get_texts()):
                text.set_color('w')
                text.set_path_effects([path_effects.Stroke(linewidth=1.5, foreground=enz_colors[k]),path_effects.Normal()])
            L = data_fit_fig[1].legend(frameon=False,handlelength=0,handletextpad=0,loc='upper right',title=f"[{sample_name}] $\mu$M")
            for k,text in enumerate(L.get_texts()):
                text.set_color('w')
                text.set_path_effects([path_effects.Stroke(linewidth=1.5, foreground=enz_colors[k]),path_effects.Normal()])

            data_fit_fig[0].tight_layout()
            normalized_data_fit_fig[0].tight_layout()
            pdf.savefig(data_fit_fig[0])
            pdf.savefig(normalized_data_fit_fig[0])
        plt.close()

    @staticmethod
    def plot_residuals(experiments, kinetic_models, hybridization_models, normalized_residuals, enz_colors, pdf):

        for j, experiment in enumerate(experiments): # Plot individual replicates on separate plots to see fits more clearly
            kinetic_model = kinetic_models[j]
            hybridization_model = hybridization_models[j]
            normalized_residual = normalized_residuals[j]

            resid_fig = plt.subplots(len(experiment.enzyme),1,figsize=(7,len(experiment.enzyme))) # One subplot for each set of residuals to see more clearly

            max_time = round(np.max([np.max(v) for v in experiment.time]),-2)
            #xlim = [0-0.03*max_time, max_time+0.03*max_time]
            #xticks = np.linspace(0,max_time,5)

            xlim = [0-0.01*max_time, 2800]
            xticks = np.linspace(0,2800,5)

            for subfig in resid_fig[1]:
                subfig.axhline(y=0, color='k',lw=1,ls='--') # Data fit residual plots

            for i, enzyme in enumerate(experiment.enzyme):
                color_idx = i
                resid_fig[1][i].errorbar(experiment.time[i][1:],normalized_residual[i],yerr=hybridization_model.normalized_fret_error[i][1:],fmt='o',markersize=8,mfc='w',mec=enz_colors[color_idx],
                                         capsize=3,capthick=1.5,ecolor=enz_colors[color_idx])
                resid_fig[1][i].set_ylim([-0.28, 0.28])
                resid_fig[1][i].set_xlim(xlim)
                resid_fig[1][i].set_xticks(xticks)

                if i < len(experiment.enzyme) - 1:
                    resid_fig[1][i].set_xticklabels([])
                else:
                    resid_fig[1][i].set_xticklabels(xticks, rotation=-45)

            if len(experiments) > 1:
                resid_fig[1][0].set_title(f"Replicate {j+1}")
            else:
                resid_fig[1][0].set_title(f"Average of replicates")

            resid_fig[1][2].set_ylabel('Residual')
            resid_fig[1][-1].set_xlabel('Time (s)')
            resid_fig[0].tight_layout()
            resid_fig[0].subplots_adjust(hspace=0.45)
            pdf.savefig(resid_fig[0])
        plt.close()

    @staticmethod
    def plot_2d_population_bars(experiments, kinetic_models, hybridization_models, enzyme_colors, t_pop_colors, pdf, timesample):

        for j, experiment in enumerate(experiments): # Plot individual replicates on separate plots to see fits more clearly
            kinetic_model = kinetic_models[j]
            hybridization_model = hybridization_models[j]

            pop_fig = []
            for enzyme in experiment.enzyme:
                pop_fig.append(plt.subplots(1,1,figsize=(7,5))) # RNA:DNA duplex population plots

            taxlist = [] # RNA population plots at time slices
            tfiglist = []
            for i, enzyme in enumerate(experiment.enzyme):
                # Species concentration bar plots at desired time points
                for ti, time in enumerate(timesample):
                    fig, ax = plt.subplots(1, 3, figsize=(11, 5), gridspec_kw={'width_ratios': [1, 1, 6]})
                    tindex = (np.abs(kinetic_model.time[i] - time)).argmin()
                    kinetic_model.calculate_total_rna_concentrations()
                    ax[0].bar(0, kinetic_model.concentrations['E'][i][tindex]/kinetic_model.enzyme[i], color=enzyme_colors[0], label='E', width=0.5)
                    ax[0].bar(0.75, kinetic_model.concentrations['E*'][i][tindex]/kinetic_model.enzyme[i], color=enzyme_colors[1], label='E*', width=0.5)
                    ax[1].bar(0.0, kinetic_model.total_rna_concentrations[f'TA{kinetic_model.n}'][i][tindex]/kinetic_model.rna, color=t_pop_colors[-1], label=f"TA$_{{{kinetic_model.n}}}$", width=0.5)
                    ax[1].bar(0.75, kinetic_model.total_rna_concentrations['A1'][i][tindex]/(kinetic_model.rna * (kinetic_model.n - 1)), color=t_pop_colors[0], label="A$_{{{1}}}$", width=0.5)

                    for q, k in enumerate(kinetic_model.total_rna_concentrations.keys()):
                        if k not in ['A1', f"TA{kinetic_model.n}"]:
                            alen = int(k.split('TA')[1])
                            ax[2].bar(q, kinetic_model.total_rna_concentrations[k][i][tindex]/kinetic_model.rna, color=t_pop_colors[q], label=f'TA$_{{{alen}}}$')
                    ax[2].invert_xaxis()
                    ax[0].set_ylabel('Fraction')
                    ax[0].set_xlabel('Enzyme states')
                    ax[1].set_xlabel('Initial RNA and AMP')
                    ax[2].set_xlabel('Product RNA')
                    ax[0].set_xticks([0, 0.75])
                    ax[0].set_xticklabels(['E', 'E*'], rotation=45)
                    ax[1].set_xticks([0, 0.75])
                    ax[1].set_xticklabels([f"TA$_{{{kinetic_model.n}}}$", 'A$_{{{1}}}$'], rotation=45)
                    ax[2].set_xticks([x for x in range(0, kinetic_model.n - 1)])
                    rna_lens = [int(k.split('TA')[1]) for k in kinetic_model.total_rna_concentrations.keys() if k not in [f'TA{kinetic_model.n}', 'A1']]
                    ax[2].set_xticklabels(['TA' + f"$_{{{v}}}$" for v in rna_lens], rotation=45)
                    ax[0].set_xlim([-0.5, 1.25])
                    ax[1].set_xlim([-0.5, 1.25])
                    ax[2].set_xlim([16.75, -0.75])
                    ax[0].set_ylim([-0.02, 1.02])
                    ax[1].set_ylim([-0.02, 1.02])
                    ax[2].set_ylim([-0.008, 0.4])
                    ax[2].set_title(f"$E_{0}$: {np.round(kinetic_model.enzyme[i]*1e6,1)}, $RNA_{0}$: {np.round(kinetic_model.rna*1e6,1)} $\mu$M, t: {np.round(kinetic_model.time[i][tindex],0)} s")
                    fig.tight_layout()
                    taxlist.append(ax)
                    tfiglist.append(fig)
                    plt.close(fig)
            for fig in tfiglist:
                pdf.savefig(fig)
        plt.close()

    @staticmethod
    def plot_3d_population_bars(experiments, kinetic_models, hybridization_models, pdf, timesample, sample_name):

        for j, experiment in enumerate(experiments): # Plot individual replicates on separate plots to see fits more clearly
            kinetic_model = kinetic_models[j]
            kinetic_model.calculate_total_rna_concentrations()
            hybridization_model = hybridization_models[j]

            # 3D surface/bar plots, e.g. x = species, y = enzyme conc., z = species fraction
            surf_figs = []
            for ti, time in enumerate(timesample):
                species_matrix = []
                resampled_species_matrix = []
                enzyme_matrix = []
                resampled_enzyme_matrix = []
                fraction_matrix = []
                resampled_fraction_matrix = []
                rna_species = [f'TA{x}' for x in range(1, experiment.n + 1)]
                fine_enz = np.linspace(kinetic_model.enzyme[1]*1e6, kinetic_model.enzyme[-1]*1e6, 10)
                resampled_species_vector = np.linspace(1, kinetic_model.n, kinetic_model.n)
                for ei, enz in enumerate(kinetic_model.enzyme):
                    if ei == 0:
                        pass
                    else:
                        tindex = (np.abs(kinetic_model.time[ei] - time)).argmin()
                        species_vector = [int(x.split('TA')[1]) for x in rna_species]
                        enzyme_vector = [enz*1e6 for x in species_vector]
                        fraction_vector = [kinetic_model.total_rna_concentrations[x][ei][tindex]/kinetic_model.rna for x in rna_species]

                        species_matrix.append(species_vector)
                        enzyme_matrix.append(enzyme_vector)
                        fraction_matrix.append(fraction_vector)
                
                for ei, enz in enumerate(fine_enz):
                    resampled_enzyme_vector = [enz for x in resampled_species_vector]
                    resampled_species_matrix.append(resampled_species_vector)
                    resampled_enzyme_matrix.append(resampled_enzyme_vector)

                surf_fig = plt.figure(figsize=(11, 7))
                surf_ax = surf_fig.gca(projection='3d')
                X = np.array(resampled_species_matrix)
                Y = np.array(resampled_enzyme_matrix)
                Z = interpolate.griddata((np.ravel(species_matrix), np.ravel(enzyme_matrix)), np.ravel(fraction_matrix), (X, Y), method='linear')

                X = np.ravel(X)
                Y = np.ravel(Y)
                Z = np.ravel(Z)

                x = np.full_like(X, 0.8)
                y = np.full_like(Y, 0.4)
                z = np.full_like(Z, 0)

                fracs = np.ravel(X.astype(float))/np.ravel(X.max())
                norm = colors.Normalize(fracs.min(), fracs.max())
                color_values = cm.coolwarm(norm(fracs.tolist()))

                surf_ax.bar3d(Y, X, z, y, x, Z, color=color_values, edgecolor='w', linewidth=0.1, shade=False)
                surf_ax.set_ylabel('RNA polyA length', labelpad=10)
                surf_ax.set_xlabel(f'[{sample_name}] $\mu$M', labelpad=10)
                surf_ax.set_zlabel('Fraction', labelpad=10)
                surf_ax.set_yticks(np.linspace(2, kinetic_model.n, 9))
                surf_ax.set_xticks(np.linspace(Y.min(), Y.max(), 10))
                surf_ax.set_ylim([X.max()+0.05*X.max(), X.min()-0.05*X.max()])
                surf_ax.set_xlim([Y.min()-0.05*Y.max(), Y.max()+0.05*Y.max()])
                surf_ax.set_zlim([-0.01, 1.01])
                surf_ax.set_title(f"Time: {time} s")

                surf_ax.xaxis.pane.fill = False
                surf_ax.yaxis.pane.fill = False
                surf_ax.zaxis.pane.fill = False
                surf_ax.xaxis.pane.set_edgecolor('w')
                surf_ax.yaxis.pane.set_edgecolor('w')
                surf_ax.zaxis.pane.set_edgecolor('w')

                surf_ax.set_box_aspect(aspect=(1.8,1.8,1))
                surf_ax.view_init(azim=-60, elev=30)
                surf_fig.tight_layout()
                surf_figs.append(surf_fig)
                plt.close(surf_fig)

            for fig in surf_figs:
                pdf.savefig(fig)
        plt.close()

    def run_plots(self):

        if self.best_fit_flag == True:
            self.plot_best_fit(self.experiments, self.kinetic_models, self.hybridization_models, self.enzyme_colors, self.sample_name, self.pdf)
        if self.residual_flag == True:
            self.plot_residuals(self.experiments, self.kinetic_models, self.hybridization_models, self.normalized_residuals, self.enzyme_colors, self.pdf)
        if self.bar_2d_flag == True:
            self.plot_2d_population_bars(self.experiments, self.kinetic_models, self.hybridization_models, self.enzyme_bar_colors, self.t_pop_colors, self.pdf, self.timesample)
        if self.bar_3d_flag == True:
            self.plot_3d_population_bars(self.experiments, self.kinetic_models, self.hybridization_models, self.pdf, self.timesample, self.sample_name)
        self.pdf.close()

    def get_colors(self, points=100, slice=1, colormap=cm.coolwarm, map_name='plot_colors', reversed=False):

        color_values = colormap(np.linspace(0, 1, points))
        color_values = color_values[0::slice]

        if reversed == True:
            color_values = color_values[::-1]

        self.addattr(map_name, color_values)

def make_pdf(pdf_name):

    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_name)

    return pdf