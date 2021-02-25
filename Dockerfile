FROM continuumio/miniconda3:4.9.2
LABEL maintainer c.sachs@fz-juelich.de

USER root

ENV PATH "$PATH:/opt/conda/bin:/bin/sbin:/usr/bin"

COPY . /tmp/package

RUN conda config --add channels conda-forge --add channels modsim && \
    conda install -y conda-build conda-verify && \
    rm -rf /var/lib/apt/lists/* && \
    cd /tmp/package && \
    conda build recipe && \
    conda install -y -c local cellsium python=3.7.10 && \
    conda clean -afy || true && \
    useradd -m user && \
    mkdir /data && \
    chown -R user:user /data && \
    echo Done

USER user

WORKDIR /data

ENTRYPOINT ["python", "-m", "cellsium"]
