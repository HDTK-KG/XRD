import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os, os.path
from scipy import optimize, interpolate, signal
from scipy.fftpack import fft, fftfreq
import itertools
import csv
from matplotlib.gridspec import GridSpec


class two_theta_omega:

  def __init__(self, sample, filedir=r"C:\Users\7863094847\experimental data\XRD", filebasename="2tw_2θ_θ.txt", xrd_lambda=1.540598):
    self.sample = sample
    self.filedir = filedir
    self.filebasename = filebasename
    self.filepath = os.path.join(self.filedir, self.sample, self.filebasename)
    self.xrd_lambda = xrd_lambda
    self.fig = None
    self.gs = None
    self.filename, self.fileext = os.path.splitext(self.filebasename)


  def load_data(self):
    df = pd.read_csv(self.filepath, skiprows = 3, skipfooter=1,engine="python", encoding="SHIFT_JIS", header=None)
    df.columns = ["2theta", "int"]
    #qvectorに変換
    df["q"] = 4 * np.pi * np.sin(df["2theta"] * np.pi / 360)/ self.xrd_lambda
    df["q_lnsp"] = np.linspace(np.min(df["q"]), np.max(df["q"]), np.size(df["q"]))
    lar_intp = interpolate.interp1d(df["q"], df["int"])
    df["int_log"] = np.log(lar_intp(df["q_lnsp"]) + 1)
    df.to_csv(os.path.join(self.filedir, self.sample, self.filename + ".csv"), index = False)
    return df


  def make_grid(self):
    self.fig = plt.figure(figsize=(7, 12))
    self.gs = GridSpec(4, 2, figure=self.fig, width_ratios=[5, 2])


  def _2tw(self, df):
    axes_2tw = self.fig.add_subplot(self.gs[0, :])
    axes_2tw.plot(df["2theta"], np.log(df["int"]+1))
    axes_2tw.set_title("2θ/ω")


  def fft(self, df):
    two_theta_min = 0.7
    two_theta_max = 4
    t_upperbound = 200 # nm
    df_trim = df.loc[df.index[(df["2theta"] > two_theta_min) & (df["2theta"] < two_theta_max)].tolist()]

    def xrd_ref_bg(q, a, b, c):
       return -a * np.log10((q - b)) + c

    param_a = np.linspace(0.1, 500, 51)
    param_b = np.linspace(-10, 0, 16)
    param_c = np.linspace(-5,5,11)

    for a, b, c in itertools.product(param_a, param_b, param_c):
      param_init = [a, b, c]
      try:
          param_opti, _ = optimize.curve_fit(xrd_ref_bg, df_trim["q_lnsp"].values, df_trim["int_log"].values, p0 = param_init)
          print(f"optimized parameter", param_opti)
          df_trim["int_bg_log"] = xrd_ref_bg(df_trim.loc[:, "q_lnsp"], *param_opti)
          df_trim["int_osci"] = df_trim["int_log"] - df_trim["int_bg_log"]
          axes_1_0 = self.fig.add_subplot(self.gs[1, 0])
          axes_1_0.plot(df_trim["q_lnsp"], df_trim["int_log"])
          axes_1_0.plot(df_trim["q_lnsp"], df_trim["int_bg_log"])
          axes_1_0.set_title("Raw data & background")
          axes_2_0 = self.fig.add_subplot(self.gs[2, 0])
          axes_2_0.plot(df_trim["q_lnsp"], df_trim["int_osci"])
          axes_2_0.set_title("residual")
          break
      except (RuntimeError):
        pass
    int_fft = fft(df_trim["int_osci"].values)
    N = len(df_trim["int_osci"])
    q_spacing = np.abs(df_trim["q_lnsp"].values[1] - df_trim["q_lnsp"].values[0])
    df_trim["q_freq"] = fftfreq(N, q_spacing)

    #ps = power spectrum
    df_trim["int_ps"] = np.abs(int_fft)
    #dq = period of oscillation 
    #q_freq = inverse of dq
    df_trim["q_period"] = 1 / df_trim["q_freq"]
    df_trim["thickness"] = 2 * np.pi * df_trim["q_freq"] * 0.1

    df_trim.to_csv(os.path.join(self.filedir, self.sample, self.filename + "_fft.csv"), index = False)

    axes_3_0 = self.fig.add_subplot(self.gs[3, 0])
    axes_3_0.plot(df_trim["thickness"], df_trim["int_ps"], "o-")
    axes_3_0.set_xlim(0, t_upperbound)
    axes_3_0.set_title("FFT")

    #### search preak ####
    fft_peak = signal.argrelmax(df_trim["int_ps"].values)
    fft_peak_value = df_trim["int_ps"].values[fft_peak]
    q_osci = 1/df_trim["q_freq"].values[fft_peak]
    thickness_nm = 2 * np.pi * 0.1 * df_trim["q_freq"].values[fft_peak]
    fft_result = np.array([fft_peak_value, q_osci, thickness_nm])
    fft_result = fft_result[:, fft_result[0,:].argsort()[::-1]]
    fft_peak_value = fft_result[0]
    q_osci = fft_result[1]
    thickness_nm = fft_result[2]

    #print(q_osci)
    #print(thickness_nm)

    for (i, x) in enumerate(fft_peak_value):
        if i == 0:
            fft_result = ""
        if(thickness_nm[i] > 0 and thickness_nm[i] < t_upperbound and x > fft_peak_value[0] * 0.2):
            fft_result += "period of q_oscillation = {:.3f}".format(q_osci[i])
            fft_result += "\nthickness = {:.2f} nm".format(thickness_nm[i])
            fft_result += "\nps = {0:.1f}".format(x)
            fft_result += "\n"

    text = f"{fft_result}"
    axes_conbined = self.fig.add_subplot(self.gs[1:4, 1])
    axes_conbined.text(0.1, 0.5, text, fontsize=8, va='center', ha='left', transform=axes_conbined.transAxes)
    axes_conbined.axis('off') 
    plt.tight_layout()



  


class rocking_curve:

  def __init__(self,  sample, filebasename, filedir=r"C:\Users\7863094847\experimental data\XRD",xrd_lambda=1.540598):
    self.sample = sample
    self.filebasename = filebasename
    self.filedir = filedir
    self.xrd_lambda = xrd_lambda
    self.filename = []
    self.fileext = []
    


  def load_path_data(self):
    df = []
    filepath = []
    for i in range(len(self.filebasename)):
      filename, fileext = os.path.splitext(self.filebasename[i])
      self.filename.append(filename)
      self.fileext.append(fileext)
      path = os.path.join(self.filedir, self.sample, self.filebasename[i])
      data = pd.read_csv(path, skiprows = 3, skipfooter=1,engine="python", encoding="SHIFT_JIS", header=None)
      data.columns = ["omega", "int"]
      data.to_csv(os.path.join(self.filedir, self.sample, self.filename[i] + ".csv"), index = False)
      df.append(data)
      filepath.append(path)
    return df, filepath


  def rocking(self, df):
    fig, axes = plt.subplots(len(df), 2, figsize=(8, len(df)*3), gridspec_kw={"width_ratios": [3, 1]})

    def lor(x, a, b, c):
      return c/((x-a)**2+b)


    # len(df) == 1 の場合、axes を2次元に変換
    if len(df) == 1:
      axes = np.expand_dims(axes, axis=0)  # 1次元配列を2次元に変換

    for i in range(len(df)):
      axes[i, 0].plot(df[i]["omega"], df[i]["int"], ".")
      #初期値設定
      a = df[i]["omega"].values[np.argmax(df[i]["int"].values)]
      b = 1/400 #半値幅0.1くらい
      c = b*np.max(df[i]["int"].values)

      param_init = [a, b, c]
      param_opti, _  = optimize.curve_fit(lor, df[i]["omega"].values, df[i]["int"].values, p0 = param_init, maxfev = 1000)
      center = "{0:.3f}".format(param_opti[0])
      FWHM="{0:.3f}".format(2 * np.sqrt(param_opti[1]))
      max_int = "{0:.3f}".format(param_opti[2]/param_opti[1])
      d = "{0:.3f}".format(self.xrd_lambda/(2*np.sin(param_opti[0]*np.pi/180)))
      fit_result = "center: {}\nFWHM: {}\nmax intensity: {}\nlatice spacing: {}".format(center, FWHM, max_int, d)
      axes[i, 0].plot(df[i]["omega"], lor(df[i]["omega"], *param_opti))
      axes[i, 1].axis('off') 
      text = f"{self.filename[i]} \n \n \n{fit_result}"
      axes[i, 1].text(0.1, 0.5, text, fontsize=12, va='center', ha='left', transform=axes[i, 1].transAxes)
      plt.tight_layout()

      df[i]["d_omega"] = df[i]["omega"] - param_opti[0]
      df[i]["lor_fit"] = lor(df[i]["omega"], *param_opti)
      df[i].to_csv(os.path.join(self.filedir, self.sample, self.filename[i] + ".csv"), index = False)
      