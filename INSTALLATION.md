# Instalação / Installation

[Português (Brasil)](#português-brasil) · [English](#english)

## Português (Brasil)

### Requisitos

- aparelho Linux **AArch64/ARM64** com Python 3, SDL2, EGL e GLES2;
- [release pública v1.0.1](https://github.com/NextOs-Ports/terraria-nextos/releases/tag/v1.0.1);
- APK legal do Terraria Android **1.4.5.6.4**, pacote
  `com.and.games505.TerrariaPaid`, contendo a ABI `arm64-v8a`;
- espaço livre no mesmo filesystem da pasta do jogo. O NXExtract preserva uma
  margem de segurança de 256 MiB além dos dados temporários necessários.

Outro APK não é aceito por nome: conteúdo, versão, ABI, tamanhos e hashes são
validados.

### Instalação nova

1. Baixe `terraria.zip` da release.
2. Extraia o ZIP diretamente na pasta de ports usada pelo seu firmware.
3. Confira se `Terraria.sh` ficou ao lado da pasta `terraria/`; não deixe uma
   pasta `terraria.zip/` ou outro nível extra entre eles.
4. Copie seu APK para `terraria/gamedata/`. O nome do APK não importa.
5. Atualize a lista de ports, se o frontend exigir, e abra `Terraria`.
6. Na primeira execução, aguarde o NXExtract validar, extrair e preparar os
   dados. Não desligue o aparelho durante essa etapa.

Layout esperado:

```text
ports/
├── Terraria.sh
└── terraria/
    ├── terraria
    ├── run.sh
    ├── extractor.json
    ├── nxextract.py
    ├── gamedata/
    │   └── seu-apk-legal-1.4.5.6.4.apk
    ├── Players/                 # criado pelo jogo
    └── Worlds/                  # criado pelo jogo
```

Depois que o marcador validado é criado, próximas inicializações reutilizam os
dados instalados. Se a instalação for interrompida, o commit transacional não
substitui uma instalação válida anterior.

### Atualização do loader

1. Saia do Terraria e confirme que não há outra instância aberta.
2. Faça backup de `terraria/Players/` e `terraria/Worlds/`.
3. Extraia o novo ZIP sobre o port existente, mantendo `gamedata/`, `Players/`
   e `Worlds/`.
4. Abra o jogo normalmente. O NXExtract revalida o estado antes do boot.

O ZIP público não contém nem remove APK, bibliotecas Android extraídas, saves
ou mundos.

### Controles e saída

Os controles de menu e gameplay são os controles Xbox/InControl originais do
Terraria e podem ser remapeados no próprio jogo.

No teclado de nomes, use D-pad para navegar, `A` ou `R3` para escolher, `B`
para apagar, `X` para alternar maiúsculas/minúsculas, `START` para confirmar
`DONE` e `SELECT` para cancelar.

Pressione **`SELECT+START` juntos** para sair imediatamente. Não é necessário
segurar por 750 ms. O combo também funciona com o teclado aberto e é consumido
antes que `START` chegue ao menu Pause.

### Solução de problemas

**NXExtract não encontrou o APK**

- Confirme que existe um arquivo `.apk` em `terraria/gamedata/`.
- Não coloque apenas um instalador dividido incompleto ou um APK de outra ABI.

**Versão incompatível**

- Use exatamente Terraria Android `1.4.5.6.4`.
- Renomear outro APK não muda sua versão nem seus hashes.

**“Device is low in storage” / pouco espaço**

- Libere espaço no filesystem que contém a pasta do port.
- A extração precisa manter o APK, uma área temporária e uma margem de
  segurança de 256 MiB até o commit terminar.

**O jogo voltou ao frontend**

- Consulte `terraria/run.log` para o launcher/runtime.
- Consulte `terraria/nxextract.log` para a preparação dos dados.
- Não publique esses logs sem revisar caminhos locais ou outros dados do
  aparelho.

**Tela ou áudio não inicializam em outro firmware**

- Não force variáveis SDL antes de coletar o log; o loader seleciona o caminho
  pelo backend que o SDL realmente conseguiu inicializar.
- Abra uma issue com firmware, modelo/SoC, resolução e o trecho relevante do
  log, sem anexar APK nem arquivos proprietários.

## English

### Requirements

- an **AArch64/ARM64** Linux handheld with Python 3, SDL2, EGL, and GLES2;
- the [public v1.0.1 release](https://github.com/NextOs-Ports/terraria-nextos/releases/tag/v1.0.1);
- a legal Terraria Android **1.4.5.6.4** APK, package
  `com.and.games505.TerrariaPaid`, containing the `arm64-v8a` ABI;
- free space on the same filesystem as the game directory. NXExtract preserves
  a 256 MiB safety margin in addition to the required temporary data.

Another APK is not accepted by filename: content, version, ABI, sizes, and
hashes are validated.

### New installation

1. Download `terraria.zip` from the release.
2. Extract the ZIP directly into the ports directory used by your firmware.
3. Check that `Terraria.sh` sits next to the `terraria/` directory; do not
   leave an extra `terraria.zip/` directory level between them.
4. Copy your APK into `terraria/gamedata/`. Its filename does not matter.
5. Refresh the ports list if your frontend requires it, then open `Terraria`.
6. On the first launch, let NXExtract verify, extract, and prepare the data. Do
   not power off the device during this stage.

Expected layout:

```text
ports/
├── Terraria.sh
└── terraria/
    ├── terraria
    ├── run.sh
    ├── extractor.json
    ├── nxextract.py
    ├── gamedata/
    │   └── your-legal-1.4.5.6.4.apk
    ├── Players/                 # created by the game
    └── Worlds/                  # created by the game
```

After the verified marker is created, later launches reuse the installed
data. If setup is interrupted, the transactional commit does not replace a
previously valid installation.

### Updating the loader

1. Exit Terraria and make sure no other instance is running.
2. Back up `terraria/Players/` and `terraria/Worlds/`.
3. Extract the new ZIP over the existing port while preserving `gamedata/`,
   `Players/`, and `Worlds/`.
4. Launch normally. NXExtract revalidates the state before boot.

The public ZIP neither contains nor removes the APK, extracted Android
libraries, saves, or worlds.

### Controls and exit

Menu and gameplay input use Terraria's original Xbox/InControl path and can be
remapped inside the game.

On the name keyboard, use the D-pad to navigate, `A` or `R3` to choose, `B` to
delete, `X` to toggle upper/lower case, `START` to confirm `DONE`, and `SELECT`
to cancel.

Press **`SELECT+START` together** to exit immediately. A 750 ms hold is not
required. The combo also works while the keyboard is open and is consumed
before `START` reaches the Pause menu.

### Troubleshooting

**NXExtract did not find the APK**

- Check that a `.apk` file exists in `terraria/gamedata/`.
- Do not provide only an incomplete split installer or an APK for another ABI.

**Incompatible version**

- Use exactly Terraria Android `1.4.5.6.4`.
- Renaming another APK does not change its version or hashes.

**“Device is low in storage”**

- Free space on the filesystem containing the port directory.
- Extraction must keep the APK, a temporary stage, and a 256 MiB safety margin
  until commit completes.

**The game returned to the frontend**

- Read `terraria/run.log` for launcher/runtime output.
- Read `terraria/nxextract.log` for data-preparation output.
- Review logs for local paths or other device information before posting them.

**Video or audio does not initialize on another firmware**

- Do not force SDL variables before collecting the log; the loader selects its
  path from the backend SDL actually initialized.
- Open an issue with firmware, device/SoC, resolution, and the relevant log
  excerpt. Never attach an APK or proprietary game files.
