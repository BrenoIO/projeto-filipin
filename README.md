# Projeto Filipin — MVP de Apoio Comunitário em Jiu-Jitsu

Repositório oficial do MVP desenvolvido para a instituição comunitária de Jiu-Jitsu "Projeto Filipin". O sistema visa digitalizar o controle de chamadas e o acompanhamento de graduação, otimizando a rotina dos instrutores na beira do tatame.

## 📌 Visão Geral
O projeto consiste em uma aplicação web com foco *mobile-first*, desenvolvida para eliminar o controle manual em papel, agilizar o registro de presenças e fornecer alertas automatizados de elegibilidade para exames de faixa.

## 🛠️ Stack Tecnológica Planejada
* **Backend:** Python com FastAPI e SQLAlchemy.
* **Banco de Dados:** PostgreSQL hospedado no Supabase.
* **Autenticação:** JWT (JSON Web Token) com criptografia bcrypt (RNF01).
* **Interface / Protótipo:** Design centrado no usuário com foco em acessibilidade e usabilidade rápida.

## 📋 Requisitos do Sistema
* **RF01:** Cadastro seguro de usuários e alunos.
* **RF02:** Chamada digital ágil via dispositivos móveis.
* **RF03:** Histórico de frequência e consolidação de dados.
* **RF04:** Alerta automatizado de elegibilidade para graduação.
* **RNF01 / RNF02:** Segurança baseada em tokens JWT e boas práticas OWASP.
* **RNF03:** Desempenho otimizado com tempo de resposta inferior a 3 segundos (PostgreSQL).

## ♿ Acessibilidade e Sustentabilidade (ODS)
* **RAC01:** Áreas de toque mínimas de 44x44px, contraste visual superior a 4.5:1 e indicação multissensorial (combinação de cor, texto e ícones para evitar dependência exclusiva de cores).
* **ODS 10 (Redução das Desigualdades - Meta 10.2):** Apoio à inclusão social e fortalecimento de projetos esportivos comunitários.

## 📱 Estrutura do Protótipo Validado
1. **Tela 1:** Login de acesso com validação JWT.
2. **Tela 2:** Chamada Digital Mobile (listagem de alunos com seletores tipo *toggle* e botão de finalização rápida).
3. **Tela 3:** Painel de Resultados e Alertas (confirmação de sucesso e selos de elegibilidade para exames).
