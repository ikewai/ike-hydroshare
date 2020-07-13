#FROM opensuse/leap:15.2
FROM ubuntu:18.04

WORKDIR /usr/src/app

# for opensuse version
#RUN zypper refresh
#RUN zypper install -y python3 python3-pip

# for ubuntu version
RUN apt -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update 
RUN apt install python3 python3-pip -y

RUN pip3 install hs_restclient

COPY RefreshHydroShareToken.py .

CMD [ "sleep", "infinity" ]