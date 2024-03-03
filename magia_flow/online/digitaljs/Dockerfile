FROM public.ecr.aws/docker/library/debian:bookworm-slim AS yosys_base
WORKDIR /work
RUN apt update
RUN apt install -y build-essential clang bison flex \
	libreadline-dev gawk tcl-dev libffi-dev git \
	graphviz xdot pkg-config python3 libboost-system-dev \
	libboost-python-dev libboost-filesystem-dev zlib1g-dev wget
# Download Source code
RUN wget -O - https://github.com/YosysHQ/yosys/archive/refs/tags/yosys-0.38.tar.gz | tar zxf -
WORKDIR /work/yosys-yosys-0.38
RUN PREFIX=/output make config-clang
RUN PREFIX=/output make
RUN PREFIX=/output make install

FROM public.ecr.aws/docker/library/node:current-bookworm AS node_app
WORKDIR /work
RUN apt-get update && apt-get install -y \
    build-essential clang bison flex \
	  libreadline-dev gawk tcl-dev libffi-dev git \
	  graphviz xdot pkg-config python3 libboost-system-dev \
	  libboost-python-dev libboost-filesystem-dev zlib1g-dev wget\
 && rm -rf /var/lib/apt/lists/*
COPY --from=yosys_base /output /usr/local
# RUN git clone https://github.com/tilk/digitaljs_online .
RUN git clone https://github.com/khwong-c/digitaljs_online -b patch-1 .
RUN yarn install
RUN sed -i /work/src/server/index.js -e "s/8080, 'localhost'/8080/"
CMD ["npm","run","server"]

FROM public.ecr.aws/nginx/nginx:mainline AS node_frontend
COPY --from=node_app /work/dist /work/dist
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 4000
