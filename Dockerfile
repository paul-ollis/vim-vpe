# ----------------------------------------------------------------------------
#  Base image.
#
#  Contains the essentials for building code, plus Python and Vim sources.
# ----------------------------------------------------------------------------
FROM python:rc-slim-buster AS build-base

COPY docker-files/apt-sources /etc/apt/sources.list.d/src-sources.list
RUN apt-get update
# Install packages for general development.
RUN apt-get install -y git build-essential

# Install dependencies to build Python.
RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev

# Install dependencies to build Vim with gui support.
RUN apt-get install -y libgtk2.0-dev libatk1.0-dev libcairo2-dev libx11-dev libxpm-dev libxt-dev

# Clean up the Apt working files.
RUN apt-get autoremove -y && apt-get clean

# Make it possible to clone repositories hosted on the local machine.
ARG HOST=172.17.0.1
COPY docker-files/id_rsa* /root/.ssh/
RUN touch /root/.ssh/known_hosts
RUN chmod 0600 /root/.ssh/known_hosts /root/.ssh/id_rsa*
RUN chmod 0700 /root/.ssh
RUN ssh-keyscan ${HOST} >> /root/.ssh/known_hosts

# Clone my local Vim and Python repositories.
WORKDIR /root
RUN git clone paul@${HOST}:develop/tracking/vim/vim 
RUN git clone paul@${HOST}:develop/tracking/python/cpython 


# ----------------------------------------------------------------------------
#  Base image for Vim-Python testing.
#
#  A build of Python and Vim.
# ----------------------------------------------------------------------------
FROM build-base AS vim80-py36

#
# Build Python interpreter that will be built into Vim.
#
WORKDIR /root/cpython
RUN git checkout v3.6.0
COPY docker-files/py-do-config do_config
RUN chmod u+x do_config
RUN ./do_config
RUN make -j5
RUN make install
RUN ldconfig
RUN python3.6 -m pip install coverage

#
# Build Vim with GUI support.
#
WORKDIR /root/vim
RUN git checkout v8.0.0700
COPY docker-files/vim-do-config do_config
RUN chmod u+x do_config
RUN ./do_config
RUN make -j5
RUN make install
RUN ldconfig

RUN groupadd -g 1000 paul
RUN useradd -rm -s /bin/bash -g paul -G sudo -u 1000 paul
USER paul
WORKDIR /home/paul/
RUN mkdir -p .vim/pack
USER root


# ----------------------------------------------------------------------------
#  Image for running Vim tests.
# ----------------------------------------------------------------------------
FROM vim80-py36 AS vpe-test

COPY admin/requirements.txt admin/test-requirements.txt ./
RUN python3.9 -m pip install -r requirements.txt -r test-requirements.txt 

USER paul
WORKDIR /home/paul/
COPY --chown=paul:paul docker-files/test-vim.rc .vimrc
COPY --chown=paul:paul docker-files/test-bash.rc .bashrc
WORKDIR /home/paul/.vim/pack/vim-vpe/test
CMD ./run_tests


# ----------------------------------------------------------------------------
#  Image for testing installation.
# ----------------------------------------------------------------------------
FROM vim80-py36 AS vpe-install

RUN apt-get install -y zip

COPY admin/requirements.txt admin/test-requirements.txt ./
RUN python3.9 -m pip install -r requirements.txt -r test-requirements.txt 

USER paul
WORKDIR /home/paul/
COPY --chown=paul:paul docker-files/install-vim.rc .vimrc
COPY --chown=paul:paul docker-files/test-bash.rc .bashrc
COPY --chown=paul:paul vim-vpe.zip .
COPY --chown=paul:paul docker-files/demo.vim .
WORKDIR /home/paul/.vim/pack
RUN unzip ~/vim-vpe.zip
CMD gvim -f -c 'source ~/demo.vim'
