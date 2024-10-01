#!/usr/bin/env python3

import etcd3
import time
import sys

# Conecte ao etcd
etcd = etcd3.client()

# Nome único do candidato (passado como argumento do script)
nome_candidato = sys.argv[1] if len(sys.argv) > 1 else 'Candidato'

# Variáveis
lider_key = '/eleicao_lider'  # Chave para identificar o líder
lider_lease = None  # Variável para armazenar o lease do líder atual


def tentar_ser_lider():
    global lider_lease

    print(f"{nome_candidato}: Tentando a liderança...")
    
    # Criar um lease (um tempo de expiração para a liderança)
    lider_lease = etcd.lease(10)  # O lease dura 10 segundos

    try:
        # Tenta colocar o nome do candidato como líder na chave /eleicao_lider
        sucesso = etcd.put_if_not_exists(lider_key, nome_candidato, lease=lider_lease)
        
        if sucesso:
            print(f"{nome_candidato}: Sou o LÍDER!")
            aguardar_termino()
        else:
            lider_atual = etcd.get(lider_key)[0].decode('utf-8')
            print(f"{nome_candidato}: {lider_atual} é o líder...")
            # Monitora mudanças na liderança
            monitorar_lider()
    except Exception as e:
        print(f"{nome_candidato}: Erro ao tentar ser líder: {e}")
        lider_lease = None


def aguardar_termino():
    # Aguarda até que o usuário pressione Enter ou CTRL+C
    try:
        input(f"{nome_candidato}: Tecle algo para terminar\n")
    except KeyboardInterrupt:
        pass
    finally:
        # Deleta a chave de líder ao terminar, permitindo que outro candidato assuma
        etcd.delete(lider_key)
        print(f"{nome_candidato}: Fim da liderança.")


def monitorar_lider():
    # Usa o watch para monitorar a chave /eleicao_lider
    print(f"{nome_candidato}: Monitorando a liderança...")
    events_iterator, cancel = etcd.watch(lider_key)

    for event in events_iterator:
        if isinstance(event, etcd3.events.DeleteEvent):
            print(f"{nome_candidato}: O líder atual saiu. Tentando a liderança novamente...")
            tentar_ser_lider()
        elif isinstance(event, etcd3.events.PutEvent):
            lider_atual = etcd.get(lider_key)[0].decode('utf-8')
            print(f"{nome_candidato}: {lider_atual} é o novo líder.")


if __name__ == "__main__":
    # Executa a tentativa de ser líder inicialmente
    tentar_ser_lider()

    # Aguarda indefinidamente para manter o processo ativo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"{nome_candidato}: Encerrando processo.")
