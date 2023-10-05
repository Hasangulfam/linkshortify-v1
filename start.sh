if [ -z $SOURCE_CODE ]
then
  echo "Cloning main Repository"
  git clone https://github.com/Hasangulfam/linkshortify-v1.git /linkshortify-v1
else
  echo "Cloning Custom Repo from $SOURCE_CODE "
  git clone $SOURCE_CODE /linkshortify-v1
fi
cd /linkshortify-v1
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 -m main
