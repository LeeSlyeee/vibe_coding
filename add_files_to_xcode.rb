begin
  require 'xcodeproj'
rescue LoadError
  system("gem install xcodeproj --user-install")
  Gem.clear_paths
  require 'xcodeproj'
end

project_path = 'ios_app/MindDiaryApp.xcodeproj'
project = Xcodeproj::Project.open(project_path)
target = project.targets.find { |t| t.name == 'MindDiaryApp' } || project.targets.first

# Main group is usually the one containing the app files
# Find the group that contains our main source files like APIService.swift
main_group = project.main_group.groups.find { |g| g.path == 'MindDiaryApp' || g.name == 'MindDiaryApp' } || project.main_group

files_to_add = [
  'KeychainHelper.swift',
  'LLMService+Model.swift',
  'LLMService+Chat.swift',
  'LLMService+Diary.swift'
]

files_to_add.each do |file_name|
  file_path = File.join(Dir.pwd, 'ios_app', file_name)
  
  # Ensure the file exists on the filesystem
  unless File.exist?(file_path)
    puts "Warning: #{file_name} does not exist on disk at #{file_path}"
    next
  end

  # Check if it's already in the project to avoid duplicates
  existing_ref = target.source_build_phase.files.find do |build_file|
    build_file.file_ref && build_file.file_ref.path == file_name
  end

  if existing_ref
    puts "#{file_name} is already in the target."
  else
    puts "Adding #{file_name} to Xcode project..."
    file_ref = main_group.new_file(file_path)
    target.source_build_phase.add_file_reference(file_ref)
  end
end

project.save
puts "Successfully updated project.pbxproj"
