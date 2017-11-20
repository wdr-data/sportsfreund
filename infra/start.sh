#!/bin/bash

minikube start --extra-config=apiserver.ServiceNodePortRange=1-50000
