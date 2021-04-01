package main

import (
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	_ "github.com/joho/godotenv/autoload"
)

type response struct {
	Videorecords []videorecords `json:"videorecords,omitempty"`
}

type videorecords struct {
	Records   string `json:"records,omitempty"`
	ID        int    `json:"id,omitempty"`
	Order     int    `json:"order,omitempty"`
	UpdatedAt string `json:"updated_at,omitempty"`
	Duration  int    `json:"duration,omitempty"`
	Hash      string `json:"hash,omitempty"`
	Filesize  int    `json:"filesize,omitempty"`
	MD5       string `json:"md5,omitempty"`
}

type recordInfo struct {
	DownloadLink string `json:"download_link,omitempty"`
	OriginalName string `json:"original_name,omitempty"`
}

func main() {
	fmt.Println("Video updating from API")
	url := "https://media-service.kz/api/videolist/" + getMac("wlan0")
	fmt.Println(url)
	resp, err := http.Get(url)
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}
	var data response
	err = json.Unmarshal(body, &data)

	dir := "/home/lm/chronos/video/"
	if err := os.MkdirAll(dir, 0666); err != nil {
		log.Fatal(err)
	}
	tempDir := "/home/lm/chronos/temp/"
	if err := os.MkdirAll(tempDir, 0666); err != nil {
		log.Fatal(err)
	}
	var serverList = make(map[string]bool)
	updated := 0
	for _, record := range data.Videorecords {
		var recordData []recordInfo
		err = json.Unmarshal([]byte(record.Records), &recordData)

		link := recordData[0].DownloadLink
		id := strconv.Itoa(record.ID)
		md5 := record.MD5
		order := record.Order
		downloadURL := "https://media-service.kz/storage/" + link
		name := fmt.Sprintf("%04d", order) + "_" + id + ".mp4"

		path := dir + name
		tempPath := tempDir + name
		shortPathMask := dir + "*" + id + ".mp4"
		oldfile := checkForFiles(shortPathMask)
		serverList[path] = true

		if _, err := os.Stat(path); err != nil {
			if oldfile != "" {
				if oldfile != path {
					os.Rename(oldfile, path)
					fmt.Printf("Rename %s to %s", oldfile, path)
					updated++
				}
			} else {
				download(downloadURL, tempPath)
				localmd5 := getMD5(tempPath)
				if localmd5 != md5 {
					fmt.Printf("after download bad md5 hash in file %s", tempPath)
					if err := exec.Command("sudo", "shutdown", "-r", "now").Run(); err != nil {
						log.Fatal(err)
					}
				}
				updated++
			}
		} else {
			localmd5 := getMD5(path)
			if localmd5 != md5 {
				fmt.Printf("bad md5 hash in file %s", path)
				os.Remove(path)
				fmt.Printf("deleted %s", path)
				download(downloadURL, tempPath)
				localmd5 = getMD5(tempPath)
				if localmd5 != md5 {
					fmt.Printf("after download bad md5 hash in file %s", tempPath)
					if err := exec.Command("sudo", "shutdown", "-r", "now").Run(); err != nil {
						log.Fatal(err)
					}
				}
				updated++
			} else {
				fmt.Printf("skipped %s", name)
			}
		}

	}
	if len(serverList) > 0 {
		osFiles := getPaths(dir)
		for _, filePath := range osFiles {
			if !serverList[filePath] {
				err = os.Remove(filePath)
				if err != nil {
					continue
				}
				fmt.Printf("Deleted %s", filePath)
				updated++
			}
		}
	}
	filesToMove := getPaths(tempDir)
	for _, file := range filesToMove {
		splittedPath := strings.Split(file, "/")
		filename := splittedPath[len(splittedPath)-1]
		if err := os.Rename(file, dir+filename); err != nil {
			log.Fatal(err)
		}
	}
	// updated counter needed for restarting KODI after some changes, we need to implement some logic for transfer files to directory which player will play from
}

func getPaths(dir string) []string {
	var files []string

	err := filepath.Walk(dir, visit(&files))
	if err != nil {
		log.Fatal(err)
	}
	return files
}

func visit(files *[]string) filepath.WalkFunc {

	return func(path string, info os.FileInfo, err error) error {

		if err != nil {
			log.Fatal(err)
		}
		if info.IsDir() {
			return nil
		}
		*files = append(*files, path)
		return nil
	}
}

func getMD5(filePath string) string {
	var returnMD5String string

	//Open the passed argument and check for any error
	file, err := os.Open(filePath)
	if err != nil {
		return "none"
	}

	//Tell the program to call the following function when the current function returns
	defer file.Close()

	//Open a new hash interface to write to
	hash := md5.New()

	//Copy the file in the hash interface and check for any error
	if _, err := io.Copy(hash, file); err != nil {
		return "none"
	}

	//Get the 16 bytes hash
	hashInBytes := hash.Sum(nil)[:16]

	//Convert the bytes to a string
	returnMD5String = hex.EncodeToString(hashInBytes)

	return returnMD5String

}

func getMac(itf string) string {

	if itf == "" {
		itf = "eth0"
	}
	fileName := fmt.Sprintf("/sys/class/net/%s/address", itf)

	var line string
	file, err := ioutil.ReadFile(fileName)
	if err != nil {
		return "None"
	}
	line = string(file)[0:17]

	return line
}

func checkForFiles(path string) string {
	files, _ := filepath.Glob(path)
	for _, v := range files {
		return v
	}
	return ""
}

func download(url, path string) {

	file, err := os.Create(path)
	if err != nil {
		return
	}
	defer file.Close()
	resp, err := http.Get(url)
	if err != nil {
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return
	}
	_, err = io.Copy(file, resp.Body)
	if err != nil {
		return
	}
}
