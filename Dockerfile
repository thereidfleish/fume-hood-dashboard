# syntax=docker/dockerfile:1

FROM python:3.11
RUN pip install pandas
RUN pip install dash
RUN pip install dash_bootstrap_components
RUN pip install dash_treeview_antd
RUN pip install dash-svg
COPY dash/ dash/
WORKDIR /dash
EXPOSE 8055
CMD python app.py
