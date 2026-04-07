FROM python:3.12

# Set working directory inside the container
WORKDIR /work

COPY requirements.txt .
RUN pip install -r requirements.txt
ENV MPLCONFIGDIR /tmp/mplconfig
RUN mkdir -p /tmp/mplconfig
RUN python -m nltk.downloader -d /nltk_data punkt_tab
USER 1000
ENTRYPOINT [ "python" ]
