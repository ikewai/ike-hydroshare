FROM opensuse/leap:15.2

WORKDIR /usr/src/app

RUN zypper refresh
RUN zypper install -y python3 python3-pip
RUN pip install hs_restclient

COPY RefreshHydroShareToken.py .

CMD [ "sleep", "infinity" ]