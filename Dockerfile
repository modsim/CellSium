FROM ubuntu:20.04

LABEL maintainer=c.sachs@fz-juelich.de

ARG DEBIAN_FRONTEND="noninteractive"
ARG MICROMAMBA="https://anaconda.org/conda-forge/micromamba/0.8.2/download/linux-64/micromamba-0.8.2-1.tar.bz2"
ARG PYTHONVERSION=3.9

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC
ENV PATH=/opt/conda/bin:${PATH}
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}

ENV PYTHONDONTWRITEBYTECODE=1

ENV CONDA_PREFIX=/opt/conda
ENV MAMBA_ROOT_PREFIX=${CONDA_PREFIX}

COPY . /tmp/package

WORKDIR /tmp/package

RUN BUILD_START=`date +%s%N` && \
    apt-get update && \
    apt-get install -y --no-install-recommends libgl1-mesa-glx ca-certificates wget && \
    rm -rf /var/lib/apt/lists/* && \
    WORKDIR=`pwd` && mkdir -p /opt/conda/bin && cd /opt/conda/bin && \
    wget -qO- $MICROMAMBA | tar xj bin/micromamba --strip-components=1 && unset MICROMAMBA && \
    micromamba install -p $MAMBA_ROOT_PREFIX \
        python=$PYTHONVERSION conda conda-build conda-verify boa \
        -c conda-forge && \
    echo "channels:\n- conda-forge\n- modsim\n" > ~/.condarc && \
    cd $WORKDIR && \
    conda mambabuild recipe && \
    mamba install -y -c local cellsium && \
    mkdir /opt/conda/packages && \
    find /opt/conda/conda-bld -name '*.tar.bz2' -exec cp {} /opt/conda/packages \; && \
    conda clean -afy || true && \
    conda build purge-all && \
    pip cache purge || true && \
    apt-get purge --autoremove -y wget && \
    useradd -m user && \
    mkdir /data && \
    chown -R user:user /data && \
    BUILD_FINISH=`date +%s%N` && \
    echo "Build done, took `perl -e "print(($BUILD_FINISH-$BUILD_START)/1000000000)"` seconds."

USER user

WORKDIR /data

ENTRYPOINT ["python", "-m", "cellsium"]
