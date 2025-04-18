# -*- coding: utf-8 -*-
"""R Convertido

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WOonbI683DnqNdymjShxykMX22nFi2RL

CÓDIGO R CONVERTIDO PARA PYTHON
"""

import os
import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# Definir diretório de trabalho
os.chdir("D:/OneDrive/09 - Mestrado/Mestrado UFABC/Dissertação/experimento/BAIXADA SANTISTA")

# Carregar dados
grid = gpd.read_file("modelo_cel_rmbs_ap.gpkg")
points = gpd.read_file("ANUNCIOS_RMBS_SHP.shp")

# Renomear colunas
points = points.rename(columns={
    'fid': 'ID',
    'field_1': 'Valor_venda',
    'field_2': 'Valor_cond',
    'field_3': 'End',
    'field_4': 'Lat',
    'field_5': 'Long',
    'field_6': 'Area',
    'field_7': 'Desc'
})

points['Valor_venda'] = pd.to_numeric(points['Valor_venda'].astype(str).str.replace(',', '.'), errors='coerce')

# Criar colunas binárias no grid
grid['tec_full'] = grid['TEC'].isin(["1", "2", "3", "4", "5", "6"]).astype(int)
grid['t12346'] = grid['TEC'].isin(["1", "2", "3", "4", "6"]).astype(int)

grid['tec_full'] = grid['tec_full'].fillna(0)
grid['t12346'] = grid['t12346'].fillna(0)

# Criar densidade de Kernel
def kde_estimation(points, grid, bandwidth=500):
    kde = gaussian_kde(points[['Long', 'Lat']].T, bw_method=bandwidth/1000)
    grid['kde_value'] = kde(grid[['geometry']].apply(lambda x: [x.x, x.y], axis=1).tolist())
    return grid

grid = kde_estimation(points, grid)

# Modelos de regressão logística
X = grid[['kde_value']]
y1 = grid['tec_full']
y2 = grid['t12346']

logit1 = sm.Logit(y1, sm.add_constant(X)).fit()
logit2 = sm.Logit(y2, sm.add_constant(X)).fit()

print(logit1.summary())
print(logit2.summary())

grid['model1'] = logit1.predict(sm.add_constant(X))
grid['model2'] = logit2.predict(sm.add_constant(X))

# Salvar resultados
grid.to_file("0_GRADE_FINAL.gpkg", driver="GPKG")

# Modelo Multinomial
grid_precarious = grid[grid['TEC'] != "0"].copy()
scaler = StandardScaler()
grid_precarious[['densidade', 'TEC_Rev']] = scaler.fit_transform(grid_precarious[['kde_value', 'DEN_OCUP']])

y_multinomial = grid_precarious['TEC']
X_multinomial = grid_precarious[['densidade', 'TEC_Rev']]

multi_model = LogisticRegression(multi_class='multinomial', solver='lbfgs')
multi_model.fit(X_multinomial, y_multinomial)

grid_precarious['predito'] = multi_model.predict(X_multinomial)
grid_precarious.to_file("grid_precarious_reg_multinomial.shp", driver="ESRI Shapefile")