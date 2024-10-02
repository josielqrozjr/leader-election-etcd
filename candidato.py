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
lock_key = '/lock_lideranca'  # Lock para evitar condição de corrida
tempo_vida = 10  # Variável para armazenar o tempo que o candidato será o líder atual


def tentarSerLider():
    
    print(f"Candidato {nome_candidato} --> Tentando a liderança...")
    
    # Tentar adquirir um lock antes de se tornar líder
    with etcd.lock(lock_key, ttl=tempo_vida):

        # Criar um tempo de expiração para a liderança
        global tempo_lease
        tempo_lease = etcd.lease(tempo_vida)  # O lease dura 10 segundos

        # Armazenar o líder atual
        lider_atual = etcd.get(lider_key)[0]

        # Verificar se já existe um líder
        if lider_atual is not None:
            lider_atual = lider_atual[0].decode('utf-8')
            print(f"O candidato {lider_atual} é o LÍDER...")
            
            # Escutar as mudanças na eleição do líder
            escutarLider()
        else:
            etcd.put(lider_key, nome_candidato, lease=tempo_lease) # Eleger candidato como líder
            print(f"Candidato {nome_candidato} --> Eu sou o LÍDER!")
            aguardarTerminar()


def aguardarTerminar():
    # Aguarda até que o usuário pressione qualquer tecla ou CTRL+C
    try:
        input(f"Candidato {nome_candidato} --> Pressione qualquer tecla para terminar\n")
        tempo_lease.refresh()

    except KeyboardInterrupt:
        pass

    finally:
        # Deleta a chave de líder ao terminar, permitindo que outro candidato assuma
        etcd.delete(lider_key)
        print(f"Candidato {nome_candidato} --> Fim da liderança!")


def escutarLider():

    # Usa o watch para monitorar a chave
    print(f"Verificando mudanças na liderança...")
    eventos, parar_escuta = etcd.watch(lider_key)

    for evento in eventos:
        if isinstance(evento, etcd3.events.DeleteEvent):
            print(f"Candidato {nome_candidato} --> O líder atual saiu.")
            tentarSerLider()
        elif isinstance(evento, etcd3.events.PutEvent):
            lider_atual = etcd.get(lider_key)[0].decode('utf-8')
            print(f"\nO candidato {lider_atual} é o NOVO LÍDER.")


if __name__ == "__main__":
    # Executa a tentativa de ser líder inicialmente
    tentarSerLider()

    # Aguarda indefinidamente para manter o processo ativo
    try:
        while True:
            time.sleep(1)
            print("AQUI no LOOP")
    except KeyboardInterrupt:
        print(f"{nome_candidato}: Encerrando processo.")