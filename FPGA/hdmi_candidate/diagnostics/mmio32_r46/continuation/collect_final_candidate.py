from pathlib import Path
W=Path(__file__).resolve().parent
source=(W/'collect.py').read_text()
source=source.replace("candidate-capture.tar.gz","candidate-capture-final.tar.gz")
source=source.replace("candidate-archive","candidate-final-archive").replace("candidate-download","candidate-final-download")
source=source.replace("E/'board-candidate'","E/'board-candidate-final'").replace("E/'candidate-result.json'","E/'candidate-final-result.json'")
exec(compile(source,str(W/'collect.py'),'exec'))
